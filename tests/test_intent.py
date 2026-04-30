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


def test_intent_inherits_previous_after_sales_on_short_confirmation() -> None:
    agent = CustomerServiceAgent()
    intent, score = agent.detect_intent("符合", previous_intent="after_sales_policy")
    assert intent == "after_sales_policy"
    assert score >= 0.8


def test_short_confirmation_without_previous_intent_falls_back() -> None:
    agent = CustomerServiceAgent()
    intent, _ = agent.detect_intent("符合")
    assert intent == "knowledge_qa"


def test_extract_order_id_from_message() -> None:
    agent = CustomerServiceAgent()
    assert agent.extract_order_id("帮我查下订单2026003现在什么状态") == "2026003"
