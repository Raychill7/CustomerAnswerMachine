from app.agent.tools import query_order_status
from app.db.repositories import init_db


def test_query_order_status_reads_seeded_demo_order() -> None:
    init_db()
    result = query_order_status("2026002")
    assert result.ok is True
    assert result.payload["order_id"] == "2026002"
    assert result.payload["status"] == "已发货"
