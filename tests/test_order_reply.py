import pytest

from app.agent.graph import CustomerServiceAgent
from app.db.repositories import init_db


class _FailLLM:
    async def chat(self, _: list[dict[str, str]]) -> dict:
        raise AssertionError("order_status should not call llm.chat")


@pytest.mark.asyncio
async def test_order_status_reply_is_deterministic() -> None:
    init_db()
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-order-reply",
        user_message="查询订单2026001",
        user_id="u1",
    )

    assert state["intent"] == "order_status"
    assert state["tool_result"]["status"] == "已送达"
    assert "已送达" in state["answer"]
