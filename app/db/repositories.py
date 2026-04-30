from pathlib import Path
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Base, ChatLog, FailureCase, Ticket

settings = get_settings()
if settings.postgres_dsn.startswith("sqlite:///"):
    sqlite_path = settings.postgres_dsn.replace("sqlite:///", "", 1)
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.postgres_dsn, pool_pre_ping=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def save_chat_log(session_id: str, user_message: str, answer: str, intent: str, confidence: float) -> None:
    with Session(engine) as session:
        row = ChatLog(
            session_id=session_id,
            user_message=user_message,
            answer=answer,
            intent=intent,
            confidence=confidence,
        )
        session.add(row)
        session.commit()


def save_ticket(ticket_id: str, session_id: str, user_id: str, topic: str, detail: str, status: str = "open") -> None:
    with Session(engine) as session:
        row = Ticket(
            ticket_id=ticket_id,
            session_id=session_id,
            user_id=user_id,
            topic=topic,
            detail=detail,
            status=status,
        )
        session.add(row)
        session.commit()


def save_failure_case(
    session_id: str,
    user_message: str,
    answer: str,
    intent: str,
    confidence: float,
    references: list[str],
    fail_reasons: list[str],
) -> None:
    with Session(engine) as session:
        row = FailureCase(
            session_id=session_id,
            user_message=user_message,
            answer=answer,
            intent=intent,
            confidence=confidence,
            references_json=json.dumps(references, ensure_ascii=False),
            fail_reasons=",".join(sorted(set(fail_reasons))),
            status="new",
        )
        session.add(row)
        session.commit()


def list_failure_cases(status: str = "new", limit: int = 50) -> list[dict]:
    with Session(engine) as session:
        rows = (
            session.query(FailureCase)
            .filter(FailureCase.status == status)
            .order_by(FailureCase.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row.id,
                "session_id": row.session_id,
                "user_message": row.user_message,
                "intent": row.intent,
                "confidence": row.confidence,
                "answer": row.answer,
                "references": json.loads(row.references_json),
                "fail_reasons": [item for item in row.fail_reasons.split(",") if item],
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
