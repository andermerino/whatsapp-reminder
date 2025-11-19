from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/messages", tags=["messages"])


# Endpoint to get all messages
@router.get("/", response_model=list[schemas.MessageOut])
def get_messages(db: Session = Depends(get_db)):
    messages = db.query(models.Message).all()
    return messages


# Endpoint to save a new message
@router.post("/", response_model=schemas.MessageOut)
def create_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    new_message = models.Message(**message.model_dump())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return {"new_message": new_message, "message": "Message created successfully"}


# Endpoint to get all user messages
@router.get("/user/{user_id}", response_model=list[schemas.MessageOut])
def get_user_messages(user_id: int, db: Session = Depends(get_db)):
    user_messages = db.query(models.Message).filter(models.Message.user_id == user_id).all()
    return user_messages


# Endpoint to get latest user message
@router.get("/user/{user_id}/latest", response_model=schemas.MessageOut)
def get_latest_user_message(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Message)
        .filter(models.Message.user_id == user_id)
        .order_by(models.Message.created_at.desc())
        .limit(5)
        .all()
    )