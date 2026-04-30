from app.db.repositories import get_order_status, init_db


def test_demo_orders_seeded_in_db() -> None:
    init_db()
    delivered = get_order_status("2026001")
    shipped = get_order_status("2026002")
    pending = get_order_status("2026003")

    assert delivered is not None
    assert shipped is not None
    assert pending is not None
    assert delivered["status"] == "已送达"
    assert shipped["status"] == "已发货"
    assert pending["status"] == "未发货"
