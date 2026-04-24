from fastapi import APIRouter

from app.agent.tools import create_human_ticket
from app.db.repositories import save_ticket
from app.schemas.ticket import TicketCreateRequest, TicketCreateResponse

router = APIRouter(prefix="/ticket", tags=["ticket"])


@router.post("", response_model=TicketCreateResponse)
async def create_ticket(req: TicketCreateRequest) -> TicketCreateResponse:
    result = create_human_ticket(
        session_id=req.session_id,
        topic=req.topic,
        detail=req.detail,
        user_id=req.user_id,
    )
    ticket_id = result.payload["ticket_id"]
    save_ticket(
        ticket_id=ticket_id,
        session_id=req.session_id,
        user_id=req.user_id,
        topic=req.topic,
        detail=req.detail,
        status="open",
    )
    return TicketCreateResponse(ticket_id=ticket_id, status="open")
