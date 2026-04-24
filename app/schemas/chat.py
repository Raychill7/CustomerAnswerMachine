from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_message: str = Field(min_length=1)
    user_id: str | None = None


class ChatAction(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    actions: list[ChatAction] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)
