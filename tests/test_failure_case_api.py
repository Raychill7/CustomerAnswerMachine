from fastapi.testclient import TestClient

from app.db.repositories import init_db, save_failure_case
from app.main import app

client = TestClient(app)


def test_get_failure_cases_returns_seeded_item() -> None:
    init_db()
    save_failure_case(
        session_id="s-test-failure",
        user_message="这个回答不对",
        answer="抱歉请稍后再试",
        intent="knowledge_qa",
        confidence=0.5,
        references=[],
        fail_reasons=["low_confidence", "no_references"],
    )
    response = client.get("/chat/failure-cases?status=new&limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert any(item["session_id"] == "s-test-failure" for item in payload["items"])
