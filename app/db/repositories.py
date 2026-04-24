from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Base, ChatLog, Ticket

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
