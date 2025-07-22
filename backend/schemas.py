from pydantic import BaseModel
from typing import Optional
from datetime import datetime

## For session_conversations

class SessionConversationBase(BaseModel):
    session_id: Optional[str] = None
    conversation_id: Optional[int] = None
    message_text: Optional[str] = None
    message_type: Optional[str] = None
    emotion: Optional[str] = None
    timestamp: Optional[datetime] = None


class SessionConversationCreate(SessionConversationBase):
    pass  # All optional fields, or make fields required if you want


class SessionConversationUpdate(SessionConversationBase):
    pass  # same as base, used for PATCH/PUT


class SessionConversationOut(SessionConversationBase):
    id: int

    class Config:
        orm_mode = True

## For user_sessions

class UserSessionBase(BaseModel):
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None


class UserSessionCreate(UserSessionBase):
    pass


class UserSessionUpdate(UserSessionBase):
    pass


class UserSessionOut(UserSessionBase):
    id: int

    class Config:
        orm_mode = True
