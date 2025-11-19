from app.models import Reminder, User
from app.tasks.reminders import schedule_reminder
from datetime import datetime, date, time
import pytz


def create_reminder(db, user: User, text: str, date: date, hour: time):
    """
    🛈 FUNCIÓN PRINCIPAL: Crear recordatorio + programar en Celery
    """
    # 1. Crear en DB
    reminder = Reminder(user_id=user.id, text=text, date=date, hour=hour)
    db.add(reminder)
    db.commit()
    
    # 2. Programar en Celery
    user_tz = pytz.timezone(user.timezone)
    reminder_datetime = user_tz.localize(datetime.combine(date, hour))
    utc_datetime = reminder_datetime.astimezone(pytz.UTC)
    
    # 🚀 AQUÍ SE PROGRAMA EN CELERY
    print("🔧 Debug - Antes de llamar schedule_reminder:")
    print(f"  - reminder_id: {reminder.id} (tipo: {type(reminder.id)})")
    print(f"  - utc_datetime: {utc_datetime} (tipo: {type(utc_datetime)})")
    print(f"  - timezone: {user.timezone} (tipo: {type(user.timezone)})")
    
    schedule_reminder.delay(reminder.id, utc_datetime, user.timezone)
    
    print(f"✅ Recordatorio creado y programado para {reminder_datetime}")
    return reminder