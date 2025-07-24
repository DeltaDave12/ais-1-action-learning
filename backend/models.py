from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SessionConversation(Base):
    __tablename__ = "session_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=True, index=True)  # changed to Integer
    last_updated = Column(TIMESTAMP(timezone=True), nullable=True)
    messages = Column(JSON, nullable=True)  # JSONB in Postgres, use SQLAlchemy JSON type
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)  # Consider storing hashed passwords, not raw text
    user_id = Column(String(50), nullable=True, index=True)
