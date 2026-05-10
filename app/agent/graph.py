import logging
import re
from typing import TypedDict

from app.agent.chat_history import ChatTurn, prepare_history_turns
from app.agent.tools import create_human_ticket, get_return_policy, query_order_status
from app.core.config import get_settings
from app.db.repositories import list_orders_for_customer
from app.llm.deepseek_client import DeepSeekClient
from app.rag.retriever import RetrievedChunk, SimpleRetriever

logger = logging.getLogger(__name__)

# Demo chat user_id → seeded customer (see README「演示订单数据」).
_CHAT_USER_TO_DEMO_CUSTOMER: dict[str, str] = {
    "demo-user": "CUST-2026-DEMO",
    "u1": "CUST-2026-DEMO",
}


def demo_customer_id_for_chat_user(user_id: str | None) -> str | None:
    if not user_id:
        return None
    return _CHAT_USER_TO_DEMO_CUSTOMER.get(user_id)


class AgentState(TypedDict):
    session_id: str
    user_message: str
    intent: str
    confidence: float
    references: list[str]
    tool_result: dict
    answer: str
    usage: dict


class CustomerServiceAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = SimpleRetriever()
        self.llm = DeepSeekClient()
        self.rewrite_aliases = {
            "报销": "发票",
            "票据": "发票",
            "凭证": "发票",
            "轨迹": "物流",
            "包裹": "快递",
            "退钱": "退款",
        }
        self.short_confirmations = {
            "好",
            "好的",
            "行",
            "可以",
            "没问题",
            "是",
            "是的",
            "对",
            "对的",
            "符合",
            "满足",
            "嗯",
            "嗯嗯",
        }
        self.condition_display_map = {
            "unused": "商品未使用",
            "original_package": "保留原包装",
        }

    @staticmethod
    def build_trace_event(
        session_id: str,
        user_message: str,
        intent: str,
        confidence: float,
        references: list[str],
        retrieved_chunks: list[RetrievedChunk],
        tool_result: dict,
        rewritten_query: str | None = None,
        retrieval_mode: str = "single",
    ) -> dict:
        return {
            "event": "agent_trace",
            "session_id": session_id,
            "user_message": user_message,
            "rewritten_query": rewritten_query,
            "retrieval_mode": retrieval_mode,
            "intent": intent,
            "confidence": confidence,
            "references": references,
            "retrieval_debug": [
                {
                    "source": chunk.source,
                    "score": round(chunk.score, 4),
                    "content_preview": chunk.content[:80],
                }
                for chunk in retrieved_chunks
            ],
            "tool_result_keys": sorted(tool_result.keys()),
        }

    def rewrite_query(self, query: str) -> str:
        rewritten = query
        for original, mapped in self.rewrite_aliases.items():
            if original in rewritten and mapped not in rewritten:
                rewritten = f"{rewritten} {mapped}"
        return rewritten

    def retrieve_with_rewrite(
        self, query: str, top_k: int = 3, min_score: float = 0.3
    ) -> tuple[list[RetrievedChunk], str]:
        rewritten_query = self.rewrite_query(query)
        primary = self.retriever.retrieve(query, top_k=top_k, min_score=min_score)
        if rewritten_query == query:
            return primary, rewritten_query

        rewritten = self.retriever.retrieve(rewritten_query, top_k=top_k, min_score=min_score)
        merged: dict[str, RetrievedChunk] = {}
        for chunk in primary + rewritten:
            existing = merged.get(chunk.source)
            if existing is None or chunk.score > existing.score:
                merged[chunk.source] = chunk
        ranked = sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]
        return ranked, rewritten_query

    def detect_intent(self, text: str, previous_intent: str | None = None) -> tuple[str, float]:
        normalized = text.strip()
        if self.extract_order_id(text):
            if previous_intent == "after_sales_policy":
                return "after_sales_policy", 0.9
            return "order_status", 0.9
        if any(k in text for k in ["退货", "退款", "换货"]):
            return "after_sales_policy", 0.9
        if any(k in text for k in ["物流", "快递", "订单"]):
            return "order_status", 0.88
        if any(k in text for k in ["人工", "投诉", "升级"]):
            return "handoff_human", 0.93
        if any(k in text for k in ["发票", "报销"]):
            return "invoice", 0.86
        if (
            previous_intent in {"after_sales_policy", "order_status", "invoice"}
            and len(normalized) <= 4
            and normalized in self.short_confirmations
        ):
            # Keep conversational continuity for short confirmations.
            return previous_intent, 0.82
        return "knowledge_qa", 0.7

    def order_lookup_requires_identifier(self, text: str) -> bool:
        """True when the user is asking to look up their order but did not give an order id."""
        if self.extract_order_id(text):
            return False
        if "我的订单" in text:
            return True
        if any(p in text for p in ("查询订单", "订单查询", "查订单", "订单状态")):
            return True
        return bool(re.search(r"查.{0,6}订单|订单.{0,6}查", text))

    @staticmethod
    def extract_order_id(text: str) -> str | None:
        match = re.search(r"20\d{5}", text)
        if not match:
            return None
        return match.group(0)

    @staticmethod
    def format_order_status_answer(tool_result: dict) -> str:
        if tool_result.get("needs_order_id"):
            return (
                "查询具体订单状态需要提供订单号（例如 2026001）。"
                "请在订单详情页复制订单号后发给我，或说明您已登录演示账号以便我列出关联订单。"
            )
        order_list = tool_result.get("order_list")
        if isinstance(order_list, list) and order_list:
            parts = [f"{item['order_id']}（{item['status']}）" for item in order_list]
            return "当前账号关联的订单：" + "、".join(parts) + "。请直接回复要查询的订单号。"
        if tool_result.get("not_found"):
            oid = tool_result.get("order_id", "")
            return f"未找到订单 {oid}，请核对订单号是否正确。"
        order_id = tool_result.get("order_id", "未知订单")
        status = tool_result.get("status", "状态未知")
        if status == "已送达":
            return f"订单{order_id}当前状态：已送达。若商品有问题，我可以继续协助您发起售后。"
        if status == "已发货":
            eta = tool_result.get("eta", "请留意物流更新")
            return f"订单{order_id}当前状态：已发货。{eta}。"
        if status == "未发货":
            return f"订单{order_id}当前状态：未发货。您可以稍后再查，或告诉我是否需要催发。"
        return f"订单{order_id}当前状态：{status}。"

    def format_after_sales_answer(self, order_id: str | None, policy: dict) -> str:
        if not order_id:
            return "可以为您处理退货。请先提供订单号（例如 2026001），我再继续为您处理。"
        conditions = policy.get("conditions", [])
        normalized_conditions = [
            self.condition_display_map.get(item, item) for item in conditions if isinstance(item, str)
        ]
        condition_text = "、".join(normalized_conditions) if normalized_conditions else "请保持商品完好"
        window_days = policy.get("window_days", 7)
        return (
            f"已收到订单{order_id}。根据当前退货规则，签收后{window_days}天内可申请退货，"
            f"且需满足：{condition_text}。如果确认符合，我将继续为您发起退货流程。"
        )

    async def run(
        self,
        session_id: str,
        user_message: str,
        user_id: str | None = None,
        previous_intent: str | None = None,
        chat_history: list[ChatTurn] | None = None,
    ) -> AgentState:
        intent, confidence = self.detect_intent(user_message, previous_intent=previous_intent)
        references: list[str] = []
        tool_result: dict = {}
        retrieved_chunks: list[RetrievedChunk] = []
        rewritten_query: str | None = None
        retrieval_mode = "single"

        if intent == "order_status":
            order_id = self.extract_order_id(user_message)
            if order_id:
                res = query_order_status(order_id=order_id)
                tool_result = dict(res.payload)
            elif self.order_lookup_requires_identifier(user_message):
                demo_cust = demo_customer_id_for_chat_user(user_id)
                if demo_cust:
                    orders = list_orders_for_customer(demo_cust)
                    tool_result = {"order_list": orders} if orders else {"needs_order_id": True}
                else:
                    tool_result = {"needs_order_id": True}
            else:
                retrieved_chunks, rewritten_query = self.retrieve_with_rewrite(
                    user_message, top_k=3, min_score=0.3
                )
                references = [c.source for c in retrieved_chunks if c.score >= 0.5]
                tool_result = {"retrieved_context": [c.content for c in retrieved_chunks]}
                retrieval_mode = "dual" if rewritten_query != user_message else "single"
        elif intent == "after_sales_policy":
            order_id = self.extract_order_id(user_message)
            policy = get_return_policy().payload
            tool_result = {"order_id": order_id, **policy}
            answer_override = self.format_after_sales_answer(order_id=order_id, policy=policy)
        elif intent == "handoff_human":
            tool_result = create_human_ticket(
                session_id=session_id,
                topic="manual_support",
                detail=user_message,
                user_id=user_id,
            ).payload
        else:
            retrieved_chunks, rewritten_query = self.retrieve_with_rewrite(
                user_message, top_k=3, min_score=0.3
            )
            references = [c.source for c in retrieved_chunks if c.score >= 0.5]
            tool_result = {"retrieved_context": [c.content for c in retrieved_chunks]}
            retrieval_mode = "dual" if rewritten_query != user_message else "single"
        order_status_faq_rag = intent == "order_status" and "retrieved_context" in tool_result
        if intent != "knowledge_qa" and not order_status_faq_rag:
            rewritten_query = None
            retrieval_mode = "single"

        logger.info(
            "agent_trace",
            extra={
                "trace": self.build_trace_event(
                    session_id=session_id,
                    user_message=user_message,
                    intent=intent,
                    confidence=confidence,
                    references=references,
                    retrieved_chunks=retrieved_chunks,
                    tool_result=tool_result,
                    rewritten_query=rewritten_query,
                    retrieval_mode=retrieval_mode,
                )
            },
        )

        if intent == "order_status" and "retrieved_context" not in tool_result:
            return AgentState(
                session_id=session_id,
                user_message=user_message,
                intent=intent,
                confidence=confidence,
                references=references,
                tool_result=tool_result,
                answer=self.format_order_status_answer(tool_result),
                usage={},
            )
        if intent == "after_sales_policy":
            return AgentState(
                session_id=session_id,
                user_message=user_message,
                intent=intent,
                confidence=confidence,
                references=references,
                tool_result=tool_result,
                answer=answer_override,
                usage={},
            )

        sys_prompt = (
            "你是电商客服助手。请基于已知工具结果回答，"
            "回答应简洁、礼貌、可执行；当信息不充分时请给出下一步建议。"
            "若提供了更早的对话记录，请保持前后说法一致并承接用户关切。"
        )
        user_payload = (
            f"用户问题: {user_message}\n"
            f"意图: {intent}\n"
            f"工具结果: {tool_result}\n"
            f"参考来源: {references}"
        )
        history_turns = prepare_history_turns(
            list(chat_history or []),
            current_intent=intent,
            previous_intent=previous_intent,
            filter_mode=self.settings.chat_history_filter,
            max_turns=self.settings.chat_history_max_turns,
            max_chars=self.settings.chat_history_max_chars,
        )
        messages: list[dict[str, str]] = [{"role": "system", "content": sys_prompt}]
        for turn in history_turns:
            messages.append({"role": "user", "content": turn["user_message"]})
            messages.append({"role": "assistant", "content": turn["answer"]})
        messages.append({"role": "user", "content": user_payload})
        result = await self.llm.chat(messages)
        answer = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        return AgentState(
            session_id=session_id,
            user_message=user_message,
            intent=intent,
            confidence=confidence,
            references=references,
            tool_result=tool_result,
            answer=answer,
            usage=usage,
        )
