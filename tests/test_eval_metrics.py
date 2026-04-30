from app.agent.graph import CustomerServiceAgent
from eval.evaluate import compute_metrics


def test_compute_metrics_includes_retrieval_and_citation_metrics() -> None:
    data = [
        {
            "query": "我想退货",
            "expected_intent": "after_sales_policy",
            "difficulty": "easy",
            "expected_sources": ["faq_return"],
        },
        {
            "query": "发票怎么开",
            "expected_intent": "invoice",
            "difficulty": "easy",
            "expected_sources": ["faq_invoice"],
        },
    ]
    metrics = compute_metrics(data, CustomerServiceAgent(), retrieval_k=3)

    assert "intent_accuracy" in metrics
    assert "recall_at_3" in metrics
    assert "citation_precision" in metrics
    assert "by_difficulty" in metrics
