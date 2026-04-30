from app.agent.graph import CustomerServiceAgent
from app.rag.retriever import RetrievedChunk


def test_build_trace_event_contains_retrieval_debug() -> None:
    event = CustomerServiceAgent.build_trace_event(
        session_id="s1",
        user_message="发票怎么开",
        intent="knowledge_qa",
        confidence=0.7,
        references=["faq_invoice"],
        retrieved_chunks=[
            RetrievedChunk(content="可在订单详情页申请电子发票", source="faq_invoice", score=0.8)
        ],
        tool_result={"retrieved_context": ["可在订单详情页申请电子发票"]},
    )

    assert event["session_id"] == "s1"
    assert event["intent"] == "knowledge_qa"
    assert event["references"] == ["faq_invoice"]
    assert event["retrieval_debug"][0]["source"] == "faq_invoice"
