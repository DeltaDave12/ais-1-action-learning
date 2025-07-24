from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, database, schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/session_conversations/", response_model=schemas.SessionConversationOut)
def create_session_conversation(conversation: schemas.SessionConversationCreate, db: Session = Depends(get_db)):
    db_entry = models.SessionConversation(**conversation.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/session_conversations/{conversation_id}", response_model=schemas.SessionConversationOut)
def read_session_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(models.SessionConversation).filter(models.SessionConversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="SessionConversation not found")
    return conversation


@app.get("/session_conversations/", response_model=List[schemas.SessionConversationOut])
def read_session_conversations(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.SessionConversation)
    if user_id:
        query = query.filter(models.SessionConversation.user_id == user_id)
    if username:
        query = query.filter(models.SessionConversation.username == username)
    return query.offset(skip).limit(limit).all()




@app.put("/session_conversations/{conversation_id}", response_model=schemas.SessionConversationOut)
def update_session_conversation(conversation_id: int, conversation_update: schemas.SessionConversationUpdate, db: Session = Depends(get_db)):
    conversation = db.query(models.SessionConversation).filter(models.SessionConversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="SessionConversation not found")
    update_data = conversation_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conversation, key, value)
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
