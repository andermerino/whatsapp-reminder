from pydantic_ai import Agent, ModelRetry, RunContext
from dataclasses import dataclass
import logfire
from pydantic import BaseModel
from app.config import get_classifier_model
from typing import List, Dict, Any


logfire.configure(send_to_logfire='never')
model = get_classifier_model()

GENERAL = "general"
REMINDER = "reminder"
UNKNOWN = "unknown"

class Intent(BaseModel):
    intent: str

@dataclass
class IntentDeps:
    user_id: int
    conversation_history: List[Dict[str, Any]]

system_prompt = f"""
    You are an intent classifier agent.  
    Your task is to identify the user’s intent from their latest message.  
    You must classify the intent into one of the following categories: {GENERAL}, {REMINDER}, or {UNKNOWN}.  

    # Rules
    - {GENERAL}: Use for greetings, personal data questions, casual conversation, and frequently asked questions.  
    - {REMINDER}: Use ONLY for messages related to reminders, alarms, calendar events, or scheduling.  
    - {UNKNOWN}: Use ONLY when the message is clearly the end of the conversation (e.g., "Adiós", "Hasta luego", "Vale") OR when the message has no meaning (random characters, nonsense).  

    # Context usage
    - You must ALWAYS call the tool `get_conversation_context` to retrieve the entire conversation history BEFORE classifying.  
    - The classification must ALWAYS take into account both:  
    1. The user’s latest message.  
    2. The full conversation context.  

    - If the conversation history contains information about reminders that have already been created, you must IGNORE that old information. Only classify based on the user’s current intent.  

    # Output
    - Respond ONLY with one of the three labels: {GENERAL}, {REMINDER}, or {UNKNOWN}.  
    - Do not add explanations, extra text, or reasoning in the output.  

    # Examples
    - "Hola, ¿cómo estás?" -> {GENERAL}  
    - "¿Qué puedes hacer?" -> {GENERAL}  
    - "¿Cuál es mi nombre?" -> {GENERAL}  
    - "¿Cuál es mi fecha de nacimiento?" -> {GENERAL}  
    - "¿Cuál es mi ocupación?" -> {GENERAL}  
    - "¿Cuál es mi género?" -> {GENERAL}  
    - "¿Cuál es mi número de teléfono?" -> {GENERAL}  
    - "¿Cuál es mi correo electrónico?" -> {GENERAL}  
    - "Recuérdame llamar a Juan" -> {REMINDER}  
    - "Necesito una alarma para mañana" -> {REMINDER}  
    - "Adiós" -> {UNKNOWN}  
    - "Vale, hasta luego" -> {UNKNOWN}  
    - "Hasta luego" -> {UNKNOWN}  
    - "Vale" -> {UNKNOWN}  
    - "asdfghjkl" -> {UNKNOWN}  

    # Language
    - The user’s messages will always be in Spanish. Classify them accordingly.  

    # Security / Privacy
    ****IMPORTANT****  
    You are strictly forbidden from sharing any user ID or user-related information at any time.  
    Never share any user data under any circumstances.  
"""


classifier_agent = Agent(
    system_prompt=system_prompt,
    model=model,
    output_type=Intent,
    deps_type=IntentDeps,
    retries=3  
)


@classifier_agent.output_validator
def validate_result(ctx: RunContext, result: Intent) -> Intent:
    if result.intent not in [GENERAL, REMINDER, UNKNOWN]:
        raise ModelRetry(
            f"Invalid intent. Please choose from `{GENERAL}`, `{REMINDER}` and `{UNKNOWN}`"
        )
    return result

@classifier_agent.tool
def get_conversation_context(ctx: RunContext) -> List[Dict[str, Any]]:
    """Obtiene el contexto de conversación del usuario"""
    history = ctx.deps.conversation_history or []
    return history
    