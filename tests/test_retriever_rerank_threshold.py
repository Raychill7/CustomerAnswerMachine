from app.rag.retriever import SimpleRetriever


def test_retriever_filters_low_score_chunks() -> None:
    retriever = SimpleRetriever()
    chunks = retriever.retrieve("今天天气怎么样", top_k=3, min_score=0.45)
    assert chunks == []


def test_retriever_rerank_boosts_dominant_intent() -> None:
    retriever = SimpleRetriever()
    chunks = retriever.retrieve("发票 报销 抬头 怎么开", top_k=1, min_score=0.0)
    assert chunks[0].source == "faq_invoice"
