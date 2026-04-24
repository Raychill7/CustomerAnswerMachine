from fastapi import APIRouter, HTTPException

from app.agent.graph import CustomerServiceAgent
from app.db.repositories import save_chat_log
from app.schemas.chat import ChatAction, ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
agent = CustomerServiceAgent()


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
