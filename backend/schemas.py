from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionConversationBase(BaseModel):
    session_id: Optional[int] = None                     # Integer now
    last_updated: Optional[datetime] = None
    messages: Optional[List[Dict[str, Any]]] = None     # List of dicts representing messages
    username: Optional[str] = None
    password: Optional[str] = None
    user_id: Optional[str] = None
    totp_secret: Optional[str] = None

class SessionConversationCreate(SessionConversationBase):
    pass  # All fields optional, or add required fields as needed

class SessionConversationUpdate(SessionConversationBase):
    pass

class SessionConversationOut(SessionConversationBase):
    id: int

    class Config:
        orm_mode = True
