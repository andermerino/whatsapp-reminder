from datetime import datetime, timezone
from celery import shared_task
from app.models import Reminder, User
from app.services.whatsapp import WhatsAppService
from app.services.openai import crear_mensaje_personalizado
import pytz

whatsapp_client = WhatsAppService()

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_whatsapp_reminder(self, reminder_id: int, db_session_data: dict = None, user_timezone: str = "UTC"):
    """
    Tarea Celery que envía un recordatorio por WhatsApp
    
    Args:
        reminder_id: ID del recordatorio a enviar
        db_session_data: Datos de la sesión de DB (opcional, para recrear la sesión)
        user_timezone: Timezone del usuario para cálculos de hora
    """
    try:
        # Recrear la sesión de DB si se proporciona
        if db_session_data:
            from app.database import SessionLocal
            db = SessionLocal()
        else:
            # Fallback: crear nueva sesión
            from app.database import get_db
            db = next(get_db())
        
        try:
            reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if not reminder:
                raise ValueError(f"Recordatorio {reminder_id} no encontrado")

             # Verificar que no se haya enviado ya
            if reminder.send:
                print(f"Recordatorio {reminder_id} ya fue enviado")
                return {"status": "already_sent", "reminder_id": reminder_id}

            # Obtener información del usuario
            user = db.query(User).filter(User.id == reminder.user_id).first()
            if not user:
                raise ValueError(f"Usuario {reminder.user_id} no encontrado")

            # Usar timezone del usuario o el proporcionado
            tz_name = user_timezone or user.timezone or "UTC"
            user_tz = pytz.timezone(tz_name)

            # Verificar si es el momento correcto para enviar
            now_utc = datetime.now(timezone.utc)
            now_user_tz = now_utc.astimezone(user_tz)

            # Crear datetime del recordatorio en el timezone del usuario
            reminder_datetime = datetime.combine(reminder.date, reminder.hour)
            reminder_datetime = user_tz.localize(reminder_datetime)

            # Logs para debugging
            print(f"🕐 Recordatorio {reminder_id} - Hora actual usuario: {now_user_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"🕐 Recordatorio {reminder_id} - Hora programada usuario: {reminder_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"🕐 Recordatorio {reminder_id} - Timezone usuario: {tz_name}")

            # Verificar si ya pasó la hora (con margen de 2 minutos)
            time_diff = (reminder_datetime - now_user_tz).total_seconds() / 60
            if time_diff > 2:
                print(f"⏰ Recordatorio {reminder_id} programado para más tarde (en {time_diff:.1f} minutos)")
                # Reprogramar para el momento exacto
                self.retry(countdown=int(time_diff * 60))
                return
            elif time_diff < -2:
                print(f"⚠️ Recordatorio {reminder_id} ya pasó hace {abs(time_diff):.1f} minutos - enviando de todas formas")

            # Crear mensaje personalizado de recordatorio
            message = crear_mensaje_personalizado(reminder.text, reminder.date, reminder.hour, user.name)
            
            # Enviar WhatsApp
            whatsapp_service = WhatsAppService()
            success = whatsapp_service.send_reminder(
                phone_number=user.phone_number,
                message=message
            )
            
            if success:
                # Marcar como enviado
                reminder.send = True
                reminder.updated_at = datetime.now(timezone.utc)
                db.commit()
                
                print(f"Recordatorio #{reminder_id} enviado exitosamente a {user.phone_number}")
                return {
                    "status": "sent", 
                    "reminder_id": reminder_id, 
                    "phone": user.phone_number,
                    "sent_at": now_utc.isoformat(),
                    "user_timezone": tz_name
                }
            else:
                raise Exception("Error al enviar recordatorio porWhatsApp")

        finally:
            # Cerrar la sesión
            db.close()

    except Exception as e:
        print(f"Error enviando recordatorio {reminder_id}: {str(e)}")
        # Reintentar la tarea
        raise self.retry(exc=e)


@shared_task(name='app.tasks.reminders.schedule_reminder')
def schedule_reminder(reminder_id: int, send_at: datetime, user_timezone: str = "UTC"):
    """
    ESTA FUNCIÓN PROGRAMA EL RECORDATORIO EN CELERY
    """
    print(f"🔧 Debug - schedule_reminder recibió:")
    print(f"  - reminder_id: {reminder_id} (tipo: {type(reminder_id)})")
    print(f"  - send_at: {send_at} (tipo: {type(send_at)})")
    print(f"  - user_timezone: {user_timezone} (tipo: {type(user_timezone)})")
    
    try:
        # Programar send_whatsapp_reminder para la hora especificada
        send_whatsapp_reminder.apply_async(
            args=[reminder_id, None, user_timezone],  # Pasar user_timezone como tercer argumento
            eta=send_at  # 🕐 "Ejecutar a esta hora exacta"
        )
        
        print(f"⏰ Recordatorio {reminder_id} programado para {send_at} (UTC) - Timezone usuario: {user_timezone}")
        return {"status": "scheduled", "reminder_id": reminder_id}
        
    except Exception as e:
        print(f"❌ Error programando: {str(e)}")
        return {"status": "error", "message": str(e)}

