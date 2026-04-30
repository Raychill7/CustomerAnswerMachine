from app.rag.retriever import SimpleRetriever


def test_hybrid_retrieval_handles_invoice_synonyms() -> None:
    retriever = SimpleRetriever()
    chunks = retriever.retrieve("报销凭证怎么申请", top_k=1)
    assert chunks[0].source == "faq_invoice"


def test_hybrid_retrieval_handles_shipping_synonyms() -> None:
    retriever = SimpleRetriever()
    chunks = retriever.retrieve("包裹轨迹查不到", top_k=1)
    assert chunks[0].source == "faq_shipping"
