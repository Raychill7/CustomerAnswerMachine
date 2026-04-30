import pytest

from app.agent.graph import CustomerServiceAgent


class _FailLLM:
    async def chat(self, _: list[dict[str, str]]) -> dict:
        raise AssertionError("after_sales flow should not call llm.chat")


@pytest.mark.asyncio
async def test_after_sales_requires_order_id_first() -> None:
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-after-sales-1",
        user_message="我要退货",
        user_id="u1",
    )

    assert state["intent"] == "after_sales_policy"
    assert "订单号" in state["answer"]


@pytest.mark.asyncio
async def test_after_sales_can_continue_with_order_id_only_message() -> None:
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-after-sales-2",
        user_message="2026001",
        user_id="u1",
        previous_intent="after_sales_policy",
    )

    assert state["intent"] == "after_sales_policy"
    assert state["tool_result"]["order_id"] == "2026001"
    assert "已收到订单2026001" in state["answer"]
    assert "unused" not in state["answer"]
    assert "original_package" not in state["answer"]
    assert "未使用" in state["answer"]
    assert "原包装" in state["answer"]
