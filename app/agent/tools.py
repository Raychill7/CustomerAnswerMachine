from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.observability.metrics import TOOL_FAILURE_COUNT


@dataclass
class ToolResult:
    name: str
    ok: bool
    payload: dict


def query_order_status(order_id: str) -> ToolResult:
    return ToolResult(
        name="query_order_status",
        ok=True,
        payload={
            "order_id": order_id,
            "status": "in_transit",
            "eta": "2 days",
        },
    )


def get_return_policy() -> ToolResult:
    return ToolResult(
        name="get_return_policy",
        ok=True,
        payload={
            "window_days": 7,
            "conditions": ["unused", "original_package"],
        },
    )


def create_human_ticket(session_id: str, topic: str, detail: str, user_id: str | None = None) -> ToolResult:
    try:
        ticket_id = f"TKT-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        return ToolResult(
            name="create_human_ticket",
            ok=True,
            payload={
                "ticket_id": ticket_id,
                "session_id": session_id,
                "user_id": user_id,
                "topic": topic,
                "detail": detail,
                "status": "open",
            },
        )
    except Exception:
        TOOL_FAILURE_COUNT.labels("create_human_ticket").inc()
        return ToolResult(
            name="create_human_ticket",
            ok=False,
            payload={"error": "ticket_create_failed"},
        )
