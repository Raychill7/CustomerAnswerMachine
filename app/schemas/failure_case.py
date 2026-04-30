from pydantic import BaseModel, Field


class FailureCaseItem(BaseModel):
    id: int
    session_id: str
    user_message: str
    intent: str
    confidence: float
    answer: str
    references: list[str] = Field(default_factory=list)
    fail_reasons: list[str] = Field(default_factory=list)
    status: str
    created_at: str


class FailureCaseListResponse(BaseModel):
    items: list[FailureCaseItem] = Field(default_factory=list)
