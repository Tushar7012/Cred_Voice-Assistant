import uuid
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.memory.models import SessionMemoryModel, Base


# --------------------------------------------------
# DB INIT
# --------------------------------------------------

def init_db():
    """
    Create tables if not exists
    """
    Base.metadata.create_all(bind=engine)
    print("PostgreSQL memory tables ready")


# --------------------------------------------------
# SESSION MANAGEMENT
# --------------------------------------------------

def create_session() -> str:
    db: Session = SessionLocal()
    session_id = str(uuid.uuid4())

    session = SessionMemoryModel(
        session_id=session_id,
        facts={},
        contradictions=[],
        history=[]
    )

    db.add(session)
    db.commit()
    db.close()

    return session_id


def get_session_memory(session_id: str) -> dict:
    """
    ALWAYS returns a dict-like memory object
    (planner & agent safe)
    """
    db: Session = SessionLocal()

    session = db.query(SessionMemoryModel).filter(
        SessionMemoryModel.session_id == session_id
    ).first()

    # Auto-create if missing
    if not session:
        session = SessionMemoryModel(
            session_id=session_id,
            facts={},
            contradictions=[],
            history=[]
        )
        db.add(session)
        db.commit()

    memory = {
        "session_id": session.session_id,
        "facts": session.facts or {},
        "contradictions": session.contradictions or [],
        "history": session.history or []
    }

    db.close()
    return memory


# --------------------------------------------------
# MEMORY UPDATES
# --------------------------------------------------

def update_fact(session_id: str, key: str, value):
    db: Session = SessionLocal()
    session = db.query(SessionMemoryModel).filter(
        SessionMemoryModel.session_id == session_id
    ).first()

    if session:
        facts = session.facts or {}
        facts[key] = value
        session.facts = facts
        db.commit()

    db.close()


def add_contradiction(session_id: str, message: str):
    db: Session = SessionLocal()
    session = db.query(SessionMemoryModel).filter(
        SessionMemoryModel.session_id == session_id
    ).first()

    if session:
        contradictions = session.contradictions or []
        contradictions.append(message)
        session.contradictions = contradictions
        db.commit()

    db.close()


def append_history(session_id: str, role: str, text: str):
    db: Session = SessionLocal()
    session = db.query(SessionMemoryModel).filter(
        SessionMemoryModel.session_id == session_id
    ).first()

    if session:
        history = session.history or []
        history.append({
            "role": role,
            "text": text
        })
        session.history = history
        db.commit()

    db.close()
