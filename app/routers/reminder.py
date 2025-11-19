from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from datetime import datetime, timezone


router = APIRouter(prefix="/reminders", tags=["reminders"])


# Endpoint to create a new reminder
@router.post("/", response_model=schemas.ReminderOut)
def create_reminder(reminder: schemas.ReminderCreate, db: Session = Depends(get_db)):
    new_reminder = models.Reminder(**reminder.model_dump())
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return {"new_reminder": new_reminder, "is_created": True}


# Endpoint to get all user reminders
@router.get("/user/{user_id}", response_model=list[schemas.ReminderOut])
def get_user_reminders(user_id: int, db: Session = Depends(get_db)):
    user_reminders = db.query(models.Reminder).filter(models.Reminder.user_id == user_id).order_by(models.Reminder.created_at.desc()).limit(5).all()
    return user_reminders


# Endpoint to get pending user reminders
@router.get("/user/{user_id}/pending", response_model=list[schemas.ReminderOut])
def get_pending_user_reminders(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Reminder)
        .filter(
            models.Reminder.user_id == user_id,
            not models.Reminder.send,
            models.Reminder.date_hour >= datetime.now(timezone.utc)
        )
        .order_by(models.Reminder.date_hour.asc())
        .all()
    )


# Endpoint to update a user reminder
@router.put("/{reminder_id}", response_model=schemas.ReminderOut)
def update_reminder(reminder_id: int, reminder: schemas.ReminderUpdate, db: Session = Depends(get_db)):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    for field, value in reminder.dict(exclude_unset=True).items():
        setattr(reminder, field, value)
    db.commit()
    db.refresh(reminder)
    return reminder


# Endpoint to delete a user reminder
@router.delete("/{reminder_id}", response_model=schemas.ReminderOut)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    return {"message": "Reminder deleted successfully"}