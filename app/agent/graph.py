from typing import TypedDict

from app.agent.tools import create_human_ticket, get_return_policy, query_order_status
from app.llm.deepseek_client import DeepSeekClient
from app.rag.retriever import SimpleRetriever


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

    def detect_intent(self, text: str) -> tuple[str, float]:
        if any(k in text for k in ["退货", "退款", "换货"]):
            return "after_sales_policy", 0.9
        if any(k in text for k in ["物流", "快递", "订单"]):
            return "order_status", 0.88
        if any(k in text for k in ["人工", "投诉", "升级"]):
            return "handoff_human", 0.93
        if any(k in text for k in ["发票", "报销"]):
            return "invoice", 0.86
        return "knowledge_qa", 0.7

    async def run(self, session_id: str, user_message: str, user_id: str | None = None) -> AgentState:
        intent, confidence = self.detect_intent(user_message)
        references: list[str] = []
        tool_result: dict = {}

        if intent == "order_status":
            tool_result = query_order_status(order_id="MOCK-10001").payload
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
            chunks = self.retriever.retrieve(user_message, top_k=2)
            references = [c.source for c in chunks if c.score >= 0.5]
            tool_result = {"retrieved_context": [c.content for c in chunks]}

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
