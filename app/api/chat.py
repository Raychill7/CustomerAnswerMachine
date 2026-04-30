from fastapi import APIRouter, HTTPException

from app.agent.graph import CustomerServiceAgent
from app.core.config import get_settings
from app.db.repositories import list_failure_cases, save_chat_log, save_failure_case
from app.schemas.chat import ChatAction, ChatRequest, ChatResponse
from app.schemas.failure_case import FailureCaseListResponse

router = APIRouter(prefix="/chat", tags=["chat"])
agent = CustomerServiceAgent()
settings = get_settings()


def detect_failure_reasons(
    intent: str, confidence: float, references: list[str], confidence_threshold: float
) -> list[str]:
    reasons: list[str] = []
    if confidence < confidence_threshold:
        reasons.append("low_confidence")
    if intent == "handoff_human":
        reasons.append("handoff_human")
    if intent == "knowledge_qa" and not references:
        reasons.append("no_references")
    return reasons


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        state = await agent.run(
            session_id=req.session_id,
            user_message=req.user_message,
            user_id=req.user_id,
        )
        save_chat_log(
            session_id=state["session_id"],
            user_message=state["user_message"],
            answer=state["answer"],
            intent=state["intent"],
            confidence=state["confidence"],
        )
        failure_reasons = detect_failure_reasons(
            intent=state["intent"],
            confidence=state["confidence"],
            references=state["references"],
            confidence_threshold=settings.failure_confidence_threshold,
        )
        if failure_reasons:
            save_failure_case(
                session_id=state["session_id"],
                user_message=state["user_message"],
                answer=state["answer"],
                intent=state["intent"],
                confidence=state["confidence"],
                references=state["references"],
                fail_reasons=failure_reasons,
            )
        actions = []
        if state["intent"] == "handoff_human" and state["tool_result"].get("ticket_id"):
            actions.append(
                ChatAction(type="ticket_created", payload={"ticket_id": state["tool_result"]["ticket_id"]})
            )
        return ChatResponse(
            answer=state["answer"],
            intent=state["intent"],
            confidence=state["confidence"],
            actions=actions,
            references=state["references"],
            usage={k: int(v) for k, v in state.get("usage", {}).items() if isinstance(v, (int, float))},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"chat_failed: {exc}") from exc


@router.get("/failure-cases", response_model=FailureCaseListResponse)
async def get_failure_cases(status: str = "new", limit: int | None = None) -> FailureCaseListResponse:
    query_limit = limit if limit is not None else settings.failure_pool_default_limit
    query_limit = max(1, min(query_limit, 200))
    items = list_failure_cases(status=status, limit=query_limit)
    return FailureCaseListResponse(items=items)
