from fastapi import APIRouter, Request, Depends
import requests
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from fastapi.responses import PlainTextResponse
from app.config import WHATSAPP_ACCESS_TOKEN
from fastapi.responses import JSONResponse
from app.models import Message, Reminder
from app.services.graph_runner import get_agent_response
from app.services.whatsapp import send_whatsapp_message, send_confirm_reminder_whatsapp, mark_whatsapp_message_as_read
from app.services.reminders_tasks import create_reminder

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

pending_reminders: dict[str, dict] = {}

# Endpoint to receive whatsapp requests
@router.post("/")
async def receive_whatsapp(request: Request,  db: Session = Depends(get_db)):
    data = await request.json()

    if "entry" in data:
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                if not messages:
                    continue
                
                # Group messages by sender
                messages_by_sender = {}
                for message in messages:
                    sender = message["from"]

                    if sender not in messages_by_sender:
                        messages_by_sender[sender] = []
                    
                    messages_by_sender[sender].append(message)

                
                # Process each sender's messages
                for sender, messages in messages_by_sender.items():
                    # Obtener usuario de la conversación
                    try:
                        user = db.query(models.User).filter(models.User.phone_number == sender).first()
                    except Exception as e:
                        print(f"❌ Error getting user: {e}")
                        user = None

                    # Mark message as read
                    last_msg = messages[-1]

                    # 1) Mark message as read
                    msg_id = last_msg.get("id")
                    if msg_id:
                        mark_whatsapp_message_as_read(msg_id)

                    if not user:
                        send_whatsapp_message(sender, 'Por favor, regístrate en la aplicación para poder ayudarte.')
                        break


                    # 2) If message is interactive
                    if last_msg.get("type") == "interactive":
                        interactive = last_msg.get("interactive", {})

                        if interactive.get("type") == "button_reply":
                            button_id = interactive["button_reply"]["id"]

                            if button_id == "accept_reminder":
                                reminder_data = pending_reminders.get(sender)
            
                                if reminder_data is None:
                                    send_whatsapp_message(sender, 'Ese recordatorio ha sido descartado anteriormente!')

                                if reminder_data and user: 
                                    try:
                                        # Los datos ya son objetos date y time
                                        reminder_date = reminder_data["date"]
                                        reminder_hour = reminder_data["hour"]
                                        
                                        print(f"🕐 Creando recordatorio - Fecha: {reminder_date}, Hora: {reminder_hour}, Usuario: {user.timezone}")
                                        
                                        create_reminder(db, user, reminder_data["text"], reminder_date, reminder_hour)

                                        pending_reminders.pop(sender,None)
                                        send_whatsapp_message(sender, 'Perfecto! Te lo recordare sin falta!')
                                    except Exception as e:
                                        print(f"❌ Error saving reminder: {e}")
                                        print(f"❌ Tipo de datos - date: {type(reminder_data['date'])}, hour: {type(reminder_data['hour'])}")
                            
                            elif button_id == "reject_reminder":
                                reminder_data = pending_reminders.get(sender)
                                if reminder_data:
                                    pending_reminders.pop(sender,None)
                                    send_whatsapp_message(sender, 'No hay problema! Lo descarto.')
                                else:
                                    send_whatsapp_message(sender, 'Ese recordatorio ya esta confirmado ✅')

                        continue


                    # 3) If message is normal text
                    if "text" in last_msg:
                        # Formatear mensajes para la API de OpenAI
                        combined_message = " ".join([msg["text"]["body"] for msg in messages])
                        print(f"\n📩 Mensaje recibido de {sender}: {combined_message}")
                        # Obtener respuesta del asistente
                        agent_response = await get_agent_response(sender, combined_message, db)
                        if agent_response is None:
                            break
                        
                        if user and agent_response.reminder_is_complete:
                            pending_reminders[sender] = {
                                    "text": agent_response.reminder_text,
                                    "date": agent_response.reminder_date,
                                    "hour": agent_response.reminder_hour,
                            }
                            
                            # Enviar mensaje de confirmación por WhatsApp
                            send_confirm_reminder_whatsapp(sender, agent_response)                    
                            break
                        
                        if user:
                            if agent_response is None:
                                break


                            try:
                                new_message = Message(
                                    user_id=user.id,
                                    user_text=combined_message,
                                    response_text=agent_response.agent_response,
                                )
                                db.add(new_message)
                                db.commit()
                                db.refresh(new_message)

                                # Enviar respuesta por WhatsApp
                                send_whatsapp_message(sender, agent_response.agent_response)
                                
                            except Exception as e:
                                print(f"❌ Error saving message: {e}")
                    

    return JSONResponse(content={"status": "ok"}, status_code=200)
                            


@router.get("/")
def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("\n🔍 VERIFICACIÓN DE WEBHOOK:")
    print(f"Mode: {mode}")
    print(f"Token recibido: '{token}'")
    print(f"Token esperado: '{WHATSAPP_ACCESS_TOKEN}'")
    print(f"Challenge: {challenge}")
    print(f"¿Tokens iguales?: {token == WHATSAPP_ACCESS_TOKEN}")
    print(f"Longitud token recibido: {len(token) if token else 0}")
    print(f"Longitud token esperado: {len(WHATSAPP_ACCESS_TOKEN) if WHATSAPP_ACCESS_TOKEN else 0}")
    
    if mode == "subscribe" and token == WHATSAPP_ACCESS_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return JSONResponse(status_code=403, content={"error": "Invalid token"})