from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas



router = APIRouter(prefix="/memories", tags=["memories"])


# Endpoint to create a new memory
@router.post("/", response_model=schemas.MemoryOut)
def create_memory(memory: schemas.MemoryCreate, db: Session = Depends(get_db)):
    new_memory = models.Memory(**memory.model_dump())
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)
    return {"new_memory": new_memory, "message": "Memory created successfully"}


# Endpoint to get all user memories
@router.get("/user/{user_id}", response_model=list[schemas.MemoryOut])
def get_user_memories(user_id: int, db: Session = Depends(get_db)):
    user_memories = db.query(models.Memory).filter(models.Memory.user_id == user_id).all()
    return user_memories


# Endpoint to get all user important memories
@router.get("/user/{user_id}/important", response_model=list[schemas.MemoryOut])
def get_user_important_memories(user_id: int, db: Session = Depends(get_db)):
    user_important_memories = db.query(models.Memory).filter(models.Memory.user_id == user_id, models.Memory.important).all()
    return user_important_memories


# Endpoint to delete a memory
@router.delete("/{memory_id}", response_model=schemas.MemoryOut)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    memory = db.query(models.Memory).filter(models.Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return {"message": "Memory deleted successfully"}
