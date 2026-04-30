import logging
import re
from typing import TypedDict

from app.agent.tools import create_human_ticket, get_return_policy, query_order_status
from app.llm.deepseek_client import DeepSeekClient
from app.rag.retriever import RetrievedChunk, SimpleRetriever

logger = logging.getLogger(__name__)


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

    @staticmethod
    def extract_order_id(text: str) -> str | None:
        match = re.search(r"20\d{5}", text)
        if not match:
            return None
        return match.group(0)

    async def run(
        self,
        session_id: str,
        user_message: str,
        user_id: str | None = None,
        previous_intent: str | None = None,
    ) -> AgentState:
        intent, confidence = self.detect_intent(user_message, previous_intent=previous_intent)
        references: list[str] = []
        tool_result: dict = {}
        retrieved_chunks: list[RetrievedChunk] = []

        if intent == "order_status":
            order_id = self.extract_order_id(user_message) or "2026002"
            tool_result = query_order_status(order_id=order_id).payload
        elif intent == "after_sales_policy":
            tool_result = get_return_policy().payload
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
        if intent != "knowledge_qa":
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

        sys_prompt = (
            "你是电商客服助手。请基于已知工具结果回答，"
            "回答应简洁、礼貌、可执行；当信息不充分时请给出下一步建议。"
        )
        user_payload = (
            f"用户问题: {user_message}\n"
            f"意图: {intent}\n"
            f"工具结果: {tool_result}\n"
            f"参考来源: {references}"
        )
        result = await self.llm.chat(
            [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_payload},
            ]
        )
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
