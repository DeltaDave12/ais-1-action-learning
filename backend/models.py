from sqlalchemy import Column, Integer, String, Text, Time, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SessionConversation(Base):
    __tablename__ = "session_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), nullable=True, index=True)
    conversation_id = Column(Integer, nullable=True, index=True)
    message_text = Column(Text, nullable=True)
    message_type = Column(String(20), nullable=True)
    emotion = Column(String(50), nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=True)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(Integer, nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_active = Column(TIMESTAMP(timezone=True), nullable=True)
