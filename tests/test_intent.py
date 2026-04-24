from app.agent.graph import CustomerServiceAgent


def test_intent_detect_return() -> None:
    agent = CustomerServiceAgent()
    intent, score = agent.detect_intent("我想申请退货")
    assert intent == "after_sales_policy"
    assert score > 0.8


def test_intent_detect_order() -> None:
    agent = CustomerServiceAgent()
    intent, _ = agent.detect_intent("帮我查一下物流")
    assert intent == "order_status"
