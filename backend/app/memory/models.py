from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SessionMemoryModel(Base):
    __tablename__ = "session_memory"

    session_id = Column(String, primary_key=True, index=True)
    facts = Column(JSON, default=dict)
    contradictions = Column(JSON, default=list)
    history = Column(JSON, default=list)
