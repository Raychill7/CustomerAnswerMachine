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


@pytest.mark.asyncio
async def test_order_status_without_id_asks_for_order_number() -> None:
    init_db()
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-order-ask",
        user_message="我要查询订单",
        user_id=None,
    )

    assert state["intent"] == "order_status"
    assert state["tool_result"].get("needs_order_id") is True
    assert "订单号" in state["answer"]


@pytest.mark.asyncio
async def test_order_status_without_id_lists_demo_orders_for_mapped_user() -> None:
    init_db()
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-order-list",
        user_message="查询订单",
        user_id="demo-user",
    )

    assert state["intent"] == "order_status"
    assert len(state["tool_result"].get("order_list", [])) == 3
    assert "2026001" in state["answer"]


@pytest.mark.asyncio
async def test_order_status_unknown_order_id_not_invented() -> None:
    init_db()
    agent = CustomerServiceAgent()
    agent.llm = _FailLLM()

    state = await agent.run(
        session_id="s-order-missing",
        user_message="订单2099999状态",
        user_id=None,
    )

    assert state["intent"] == "order_status"
    assert state["tool_result"].get("not_found") is True
    assert "未找到" in state["answer"]
