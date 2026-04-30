from pathlib import Path
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Base, ChatLog, Customer, FailureCase, Order, Ticket

settings = get_settings()
if settings.postgres_dsn.startswith("sqlite:///"):
    sqlite_path = settings.postgres_dsn.replace("sqlite:///", "", 1)
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.postgres_dsn, pool_pre_ping=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    seed_demo_orders()


def seed_demo_orders() -> None:
    demo_customer_id = "CUST-2026-DEMO"
    demo_orders = [
        ("2026001", "已送达"),
        ("2026002", "已发货"),
        ("2026003", "未发货"),
    ]
    with Session(engine) as session:
        customer_exists = (
            session.query(Customer.customer_id).filter(Customer.customer_id == demo_customer_id).first()
        )
        if not customer_exists:
            session.add(Customer(customer_id=demo_customer_id, name="演示客户"))
            session.commit()

        for order_id, status in demo_orders:
            exists = session.query(Order.order_id).filter(Order.order_id == order_id).first()
            if not exists:
                session.add(Order(order_id=order_id, customer_id=demo_customer_id, status=status))
        session.commit()


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


def get_latest_intent(session_id: str) -> str | None:
    with Session(engine) as session:
        row = (
            session.query(ChatLog.intent)
            .filter(ChatLog.session_id == session_id)
            .order_by(ChatLog.created_at.desc())
            .first()
        )
        if not row:
            return None
        return row[0]


def get_order_status(order_id: str) -> dict | None:
    # Ensure demo data exists even on long-lived databases.
    seed_demo_orders()
    with Session(engine) as session:
        row = (
            session.query(Order.order_id, Order.customer_id, Order.status)
            .filter(Order.order_id == order_id)
            .first()
        )
        if not row:
            return None
        return {
            "order_id": row[0],
            "customer_id": row[1],
            "status": row[2],
        }
