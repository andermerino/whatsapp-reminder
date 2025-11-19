from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime, time


# User Input: validation schemas for User[Post]
class UserCreate(BaseModel):
    phone_number: str
    name: str
    surname: Optional[str] = None
    email: EmailStr
    timezone: str = "UTC"
    silent_mode: bool = False
    language: str = "es"
    birth_date: Optional[date] = None

# User Update: validation schemas for User[Put]
class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    silent_mode: Optional[bool] = None
    language: Optional[str] = None
    birth_date: Optional[date] = None

# User Output: schema for User[Get]
class UserOut(UserCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)




# Message Input: validation schemas for Message[Post]
class MessageCreate(BaseModel):
    user_id: int
    user_text: str
    response_text: str

# Message Output: schema for Message[Get]
class MessageOut(MessageCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)




# Reminder Input: validation schemas for Reminder[Post]
class ReminderCreate(BaseModel):
    user_id: int
    text: str
    date: date
    hour: time
    send: Optional[bool] = False

# Reminder Update: validation schemas for Reminder[Put]
class ReminderUpdate(BaseModel):
    text: Optional[str] = None
    date: Optional[date] = None
    hour: Optional[time] = None
    send: Optional[bool] = None

# Reminder Output: schema for Reminder[Get]
class ReminderOut(ReminderCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)




# Memory Input: validation schemas for Memory[Post]
class MemoryCreate(BaseModel):
    user_id: int
    key: str
    value: str
    important: Optional[bool] = False

# Memory Update: validation schemas for Memory[Put]
class MemoryUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    important: Optional[bool] = None

# Memory Output: schema for Memory[Get]
class MemoryOut(MemoryCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)