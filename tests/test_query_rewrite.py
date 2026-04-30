from app.agent.graph import CustomerServiceAgent


def test_rewrite_query_expands_invoice_terms() -> None:
    agent = CustomerServiceAgent()
    rewritten = agent.rewrite_query("报销凭证怎么弄")
    assert "发票" in rewritten


def test_dual_retrieve_merges_original_and_rewritten() -> None:
    agent = CustomerServiceAgent()
    chunks, rewritten = agent.retrieve_with_rewrite("报销票据申请", top_k=3, min_score=0.2)
    assert rewritten != "报销票据申请"
    assert any(chunk.source == "faq_invoice" for chunk in chunks)
