from app.db.repositories import get_order_status, init_db, list_orders_for_customer


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


def test_list_orders_for_demo_customer() -> None:
    init_db()
    rows = list_orders_for_customer("CUST-2026-DEMO")
    ids = {r["order_id"] for r in rows}
    assert ids == {"2026001", "2026002", "2026003"}
