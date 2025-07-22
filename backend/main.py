from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, database, schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- SessionConversation CRUD ----------

@app.post("/session_conversations/", response_model=schemas.SessionConversationOut)
def create_session_conversation(
    conversation: schemas.SessionConversationCreate, db: Session = Depends(get_db)
):
    db_conversation = models.SessionConversation(**conversation.dict())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@app.get("/session_conversations/{conversation_id}", response_model=schemas.SessionConversationOut)
def read_session_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(models.SessionConversation).filter(models.SessionConversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="SessionConversation not found")
    return conversation

@app.get("/session_conversations/", response_model=List[schemas.SessionConversationOut])
def read_session_conversations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.SessionConversation).offset(skip).limit(limit).all()

@app.put("/session_conversations/{conversation_id}", response_model=schemas.SessionConversationOut)
def update_session_conversation(
    conversation_id: int, conversation_update: schemas.SessionConversationUpdate, db: Session = Depends(get_db)
):
    conversation = db.query(models.SessionConversation).filter(models.SessionConversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="SessionConversation not found")
    for var, value in vars(conversation_update).items():
        if value is not None:
            setattr(conversation, var, value)
    db.commit()
    db.refresh(conversation)
    return conversation

@app.delete("/session_conversations/{conversation_id}")
def delete_session_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(models.SessionConversation).filter(models.SessionConversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="SessionConversation not found")
    db.delete(conversation)
    db.commit()
    return {"detail": "SessionConversation deleted"}


# ---------- UserSession CRUD ----------

@app.post("/user_sessions/", response_model=schemas.UserSessionOut)
def create_user_session(user_session: schemas.UserSessionCreate, db: Session = Depends(get_db)):
    db_session = models.UserSession(**user_session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/user_sessions/{user_session_id}", response_model=schemas.UserSessionOut)
def read_user_session(user_session_id: int, db: Session = Depends(get_db)):
    user_session = db.query(models.UserSession).filter(models.UserSession.id == user_session_id).first()
    if user_session is None:
        raise HTTPException(status_code=404, detail="UserSession not found")
    return user_session

@app.get("/user_sessions/", response_model=List[schemas.UserSessionOut])
def read_user_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.UserSession).offset(skip).limit(limit).all()

@app.put("/user_sessions/{user_session_id}", response_model=schemas.UserSessionOut)
def update_user_session(
    user_session_id: int, user_session_update: schemas.UserSessionUpdate, db: Session = Depends(get_db)
):
    user_session = db.query(models.UserSession).filter(models.UserSession.id == user_session_id).first()
    if user_session is None:
        raise HTTPException(status_code=404, detail="UserSession not found")
    for var, value in vars(user_session_update).items():
        if value is not None:
            setattr(user_session, var, value)
    db.commit()
    db.refresh(user_session)
    return user_session

@app.delete("/user_sessions/{user_session_id}")
def delete_user_session(user_session_id: int, db: Session = Depends(get_db)):
    user_session = db.query(models.UserSession).filter(models.UserSession.id == user_session_id).first()
    if user_session is None:
        raise HTTPException(status_code=404, detail="UserSession not found")
    db.delete(user_session)
    db.commit()
    return {"detail": "UserSession deleted"}
