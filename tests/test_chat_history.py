import pytest

from app.agent.chat_history import ChatTurn, prepare_history_turns
from app.agent.graph import CustomerServiceAgent


def _turn(user: str, answer: str, intent: str) -> ChatTurn:
    return {"user_message": user, "answer": answer, "intent": intent}


def test_prepare_history_turns_respects_max_turns() -> None:
    turns = [_turn(f"u{i}", f"a{i}", "knowledge_qa") for i in range(5)]
    out = prepare_history_turns(
        turns,
        current_intent="knowledge_qa",
        previous_intent=None,
        filter_mode="all",
        max_turns=2,
        max_chars=100_000,
    )
    assert len(out) == 2
    assert out[0]["user_message"] == "u3"
    assert out[1]["user_message"] == "u4"


def test_prepare_history_turns_trims_by_chars_from_oldest() -> None:
    turns = [
        _turn("aa", "bb", "knowledge_qa"),
        _turn("cccc", "dddd", "knowledge_qa"),
    ]
    out = prepare_history_turns(
        turns,
        current_intent="knowledge_qa",
        previous_intent=None,
        filter_mode="all",
        max_turns=10,
        max_chars=len("cccc") + len("dddd"),
    )
    assert len(out) == 1
    assert out[0]["user_message"] == "cccc"


def test_prepare_history_turns_intent_related_keeps_matching_intents() -> None:
    turns = [
        _turn("查物流", "好的", "order_status"),
        _turn("发票怎么开", "请提供抬头", "invoice"),
        _turn("抬头是某某公司", "收到", "invoice"),
    ]
    out = prepare_history_turns(
        turns,
        current_intent="invoice",
        previous_intent="knowledge_qa",
        filter_mode="intent_related",
        max_turns=10,
        max_chars=10_000,
    )
    assert len(out) == 2
    assert out[0]["user_message"] == "发票怎么开"


def test_prepare_history_turns_intent_related_fallback_when_empty() -> None:
    turns = [
        _turn("a", "b", "order_status"),
        _turn("c", "d", "order_status"),
        _turn("e", "f", "invoice"),
    ]
    out = prepare_history_turns(
        turns,
        current_intent="handoff_human",
        previous_intent="knowledge_qa",
        filter_mode="intent_related",
        max_turns=10,
        max_chars=10_000,
    )
    assert len(out) <= 3
    assert out[-1]["user_message"] == "e"


class _CaptureLLM:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] | None = None

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> dict:
        self.messages = messages
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}


@pytest.mark.asyncio
async def test_agent_includes_chat_history_in_llm_messages() -> None:
    agent = CustomerServiceAgent()
    cap = _CaptureLLM()
    agent.llm = cap
    history: list[ChatTurn] = [_turn("上次问了运费", "首重10元", "knowledge_qa")]
    state = await agent.run(
        session_id="s-history-1",
        user_message="那续重呢",
        user_id="u1",
        previous_intent="knowledge_qa",
        chat_history=history,
    )
    assert state["answer"] == "ok"
    assert cap.messages is not None
    assert cap.messages[0]["role"] == "system"
    assert cap.messages[1] == {"role": "user", "content": "上次问了运费"}
    assert cap.messages[2] == {"role": "assistant", "content": "首重10元"}
    assert cap.messages[-1]["role"] == "user"
    assert "续重" in cap.messages[-1]["content"]
