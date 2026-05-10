from app.agent.tools import query_order_status
from app.db.repositories import init_db


def test_query_order_status_reads_seeded_demo_order() -> None:
    init_db()
    result = query_order_status("2026002")
    assert result.ok is True
    assert result.payload["order_id"] == "2026002"
    assert result.payload["status"] == "已发货"


def test_query_order_status_unknown_order_not_invented() -> None:
    init_db()
    result = query_order_status("2099999")
    assert result.ok is False
    assert result.payload.get("not_found") is True
    assert result.payload["order_id"] == "2099999"
