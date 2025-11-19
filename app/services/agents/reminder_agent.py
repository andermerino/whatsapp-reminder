from pydantic_ai import Agent,ModelRetry, RunContext
from dataclasses import dataclass
from datetime import date, time, timezone as tz, datetime
from pydantic import BaseModel
from app.config import get_model
from typing import List, Dict, Any



# logfire.configure(send_to_logfire='never')
model = get_model()


class ReminderResponse(BaseModel):
    """Response model for the Reminder Checker agent."""
    user_id: int
    agent_response: str
    reminder_text: str
    reminder_date: date  # YYYY-MM-DD format
    reminder_hour: time  # HH:MM format
    reminder_is_complete: bool = False
 
@dataclass
class ReminderDeps:
    user_id: int
    timezone: tz = tz.utc
    conversation_history: List[Dict[str, Any]] = None

system_prompt="""
    You are a Reminder Assistant. Your goal is to help the user create clear, complete reminders.

    🚫 DO NOT invent, assume, or fill in default values for date or time.  
    ✅ Only accept date and time when the user states them explicitly and unambiguously.  

    # Tools
    - You must ALWAYS use `get_conversation_context` to have the full context of the conversation in order to better understand the reminder.  
    - If the conversation history contains information about a reminder that was already created or saved before, you must IGNORE it and only consider the user’s current request.  
    - Use `get_active_reminders` ONLY when the user explicitly asks to view their pending reminders; never reconstruct a reminders list from conversation context.  
    - You must ALWAYS call `get_today_date` to determine the current day and year, and use it to resolve any relative expressions like 'mañana', 'el jueves', 'next Monday', etc., into an absolute YYYY-MM-DD date.  

    # Language Policy
    - All clarifying questions to the user must always be asked in **Spanish**, short and direct.  
    - The final JSON field `agent_response` must also be a brief Spanish confirmation.  

    # Core Behavior
    1. Parse the user’s message and determine whether the THREE required elements are present:  
    - Reminder text (what to remember).  
    - A specific date.  
    - A specific time.  

    2. If ANY of these elements is missing or ambiguous:  
    - Ask exactly and only for the missing piece(s), in Spanish, briefly and directly.  
    - Do NOT propose, suggest, or assume any default time or date.  
    - Set `reminder_is_complete` to `false`.  

    3. If the message clearly contains all three (text, specific date, specific time) with no ambiguity:  
    - Return ONLY the following JSON object (no extra text):  
        {
        "user_id": "[id del usuario]",
        "agent_response": "[breve confirmación en español]",
        "reminder_text": "[clear, concise reminder text]",
        "reminder_date": "[YYYY-MM-DD]",
        "reminder_hour": "[HH:MM]",
        "reminder_is_complete": true
        }

    4. Ambiguity rules:  
    - “por la tarde”, “a primera hora”, “sobre las 9” → ambiguous → ask for an exact HH:MM.  
    - “el jueves” or “mañana” → resolve to YYYY-MM-DD using `get_today_date`. If unclear, ask.  
    - Multiple candidate dates/times → ask the user to choose one exact date/time.  
    - If reminder text itself is unclear → ask to clarify the text first.  

    # Output Format
    - If something is missing or ambiguous → output ONLY the JSON structure with:  
    - `reminder_is_complete = false`,  
    - `agent_response` containing the Spanish clarifying question,  
    - missing fields left empty/null.  
    - If everything is clear → output ONLY the JSON with all fields completed.  
    - Never mix a clarifying question and a complete JSON in the same response.  
    - `reminder_text` must be concise and action-oriented (e.g., “llamar al médico”, “regar las plantas”).  

    # Examples
    Input: "Recuérdame regar las plantas."  
    Output:  
    {
    "user_id": "[id del usuario]",
    "agent_response": "¿Para qué fecha y a qué hora quieres que te recuerde regar las plantas?",
    "reminder_text": "",
    "reminder_date": null,
    "reminder_hour": null,
    "reminder_is_complete": false
    }

    Input: "Recuérdame comprar pan el jueves."  
    Output:  
    {
    "user_id": "[id del usuario]",
    "agent_response": "¿A qué hora quieres que te recuerde comprar pan el jueves?",
    "reminder_text": "comprar pan",
    "reminder_date": "[YYYY-MM-DD del jueves]",
    "reminder_hour": null,
    "reminder_is_complete": false
    }

    Input: "Recuérdame llamar al médico el jueves a las 12:30."  
    Output:  
    {
    "user_id": "[id del usuario]",
    "agent_response": "De acuerdo, crearé el recordatorio.",
    "reminder_text": "llamar al médico",
    "reminder_date": "[YYYY-MM-DD del jueves]",
    "reminder_hour": "12:30",
    "reminder_is_complete": true
    }

    Input: "Quiero crear un nuevo recordatorio"  
    Output:  
    {
    "user_id": "[id del usuario]",
    "agent_response": "Claro que sí, dime qué quieres que te recuerde",
    "reminder_text": "",
    "reminder_date": null,
    "reminder_hour": null,
    "reminder_is_complete": false
    }

    # Anti-hallucination Rules
    - You must NEVER propose or auto-complete a default hour such as “09:00”, “11:00”, “12:00” or any other round time unless the user explicitly states it.  
    - If the user’s message does not contain a specific HH:MM, you MUST always ask them directly for the exact time in Spanish.  
    - Do not assume that vague expressions (“por la tarde”, “a primera hora”, “en la mañana”) map to a specific hour — instead, always ask the user for clarification.  
    - A reminder is incomplete until you have a clear text, a specific YYYY-MM-DD date, and an exact HH:MM time provided by the user.  

    # Security / Privacy
    ****IMPORTANT****  
    You are strictly forbidden from sharing any user ID or user-related information at any time. Never share any user data under any circumstances.
    """

reminder_agent = Agent(
    model=model,    
    system_prompt=system_prompt,
    output_type=ReminderResponse,
    deps_type=ReminderDeps,
    retries=3
)

@reminder_agent.output_validator
def validate_result(ctx: RunContext, result: ReminderResponse) -> ReminderResponse:
    if result.reminder_is_complete:
        remi_text = result.reminder_text
        remi_hour = result.reminder_hour
        remi_date = result.reminder_date

        if not remi_text:
            raise ModelRetry(
                "Invalid Reminder. The reminder text is empty please ask again about it."
            )
        if not remi_hour:
            raise ModelRetry(
                "Invalid Reminder. The reminder hour is empty please ask again about it."
            )
        if not remi_date:
            raise ModelRetry(
                "Invalid Reminder. The reminder date is empty please ask again about it."
            )
    return result

# --- Tools ---

@reminder_agent.tool
def get_today_date(ctx: RunContext) -> datetime:
    now = datetime.now(ctx.deps.timezone or tz.UTC)
    return now.strftime("%A %d/%m/%Y %H:%M")


@reminder_agent.tool
def get_user_id(ctx: RunContext) -> int:
    return ctx.deps.user_id

@reminder_agent.tool
def get_conversation_context(ctx: RunContext) -> List[Dict[str, Any]]:
    """Obtiene el contexto de conversación del usuario"""
    history = ctx.deps.conversation_history or []
    return history


@reminder_agent.tool
def get_active_reminders(ctx: RunContext) -> List[Dict[str, Any]]:
    """Obtiene los recordatarios activos del usuario"""
    print("Recopilando los recordatorios")
    user_id = ctx.deps.user_id
    # Importar las dependencias necesarias
    from app.database import get_db
    from app import models
    
    # Obtener la sesión de base de datos
    db = next(get_db())

    try:
        reminders = db.query(models.Reminder).filter(models.Reminder.user_id == user_id, not models.Reminder.send).all()

        reminders_list = []
        for reminder in reminders:
            reminders_list.append({
                "id": reminder.id,
                "text": reminder.text,
                "date": reminder.date.isoformat() if reminder.date else None,
                "hour": reminder.hour.isoformat() if reminder.hour else None,
                "created_at": reminder.created_at.isoformat() if reminder.created_at else None
            })
        
        if not reminders_list:
            return "No hay reminders activos"
        else:
            return reminders_list

    except Exception as e:
        # En caso de error, retornar lista vacía
        return "No hay reminders activos"
    finally:
        # Cerrar la sesión de base de datos
        db.close()