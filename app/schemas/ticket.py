from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    detail: str = Field(min_length=1)


class TicketCreateResponse(BaseModel):
    ticket_id: str
    status: str
