from datetime import datetime, timezone
import pytz
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from sqlalchemy.types import UnicodeText
from .database import Base
from app.config import FERNET_KEY


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    silent_mode = Column(Boolean, default=False)
    language = Column(String(2), default="es")
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    reminders = relationship("Reminder", back_populates="user")
    messages = relationship("Message", back_populates="user")
    memories = relationship("Memory", back_populates="user")

    def get_timezone_obj(self):
        """Convierte el string timezone a objeto pytz."""
        try:
            return pytz.timezone(self.timezone)
        except (pytz.exceptions.UnknownTimeZoneError, ValueError):
            return pytz.UTC
       

class Reminder(Base):
    __tablename__ = "reminder"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    text = Column(StringEncryptedType(UnicodeText, FERNET_KEY, FernetEngine), nullable=False)
    date = Column(Date)
    hour = Column(Time)
    send = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="reminders")


class Message(Base):
    __tablename__ = "message"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user_text = Column(StringEncryptedType(UnicodeText, FERNET_KEY, FernetEngine), nullable=False)
    response_text = Column(StringEncryptedType(UnicodeText, FERNET_KEY, FernetEngine), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="messages")



class Memory(Base):
    __tablename__ = "memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    important = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="memories")
    
    
    
    
    
    
    
    
    

    
    
    