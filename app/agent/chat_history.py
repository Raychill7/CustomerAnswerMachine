from typing import Literal, TypedDict


class ChatTurn(TypedDict):
    user_message: str
    answer: str
    intent: str


def _trim_turns_by_chars(turns: list[ChatTurn], max_chars: int) -> list[ChatTurn]:
    if max_chars <= 0 or not turns:
        return []
    kept: list[ChatTurn] = []
    total = 0
    for t in reversed(turns):
        chunk = len(t["user_message"]) + len(t["answer"])
        if not kept:
            kept.append(t)
            total = chunk
            continue
        if total + chunk > max_chars:
            break
        kept.append(t)
        total += chunk
    return list(reversed(kept))


def prepare_history_turns(
    turns: list[ChatTurn],
    *,
    current_intent: str,
    previous_intent: str | None,
    filter_mode: Literal["all", "intent_related"],
    max_turns: int,
    max_chars: int,
) -> list[ChatTurn]:
    if not turns:
        return []
    working = list(turns)
    if filter_mode == "intent_related":
        keys = {current_intent}
        if previous_intent:
            keys.add(previous_intent)
        filtered = [t for t in working if t["intent"] in keys]
        if not filtered:
            tail = min(3, max_turns) if max_turns > 0 else 0
            filtered = working[-tail:] if tail else []
        working = filtered
    if max_turns > 0:
        working = working[-max_turns:]
    else:
        working = []
    return _trim_turns_by_chars(working, max_chars)
