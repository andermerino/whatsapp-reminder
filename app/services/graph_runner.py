from app.services.agents.agent_graph import agent_graph
from app.models import User, Message
from sqlalchemy.orm import Session
from datetime import timezone as dt_timezone, datetime, timedelta


user_states = {}


def get_user_conversation_history(user_id: int, db: Session):
    try:
        last_five_messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at.desc()).limit(5).all()
        
        conversation_history = []

        for msg in reversed(last_five_messages):
            conversation_history.append({
                "role": "user",
                "content": msg.user_text
            })
            conversation_history.append({
                "role": "assistant",
                "content": msg.response_text
            })

        return conversation_history
    except Exception as e:
        print(f"❌ Error getting user conversation history: {e}")
        return []

async def get_agent_response(phone_number: str, user_input: str, db: Session):

    cleanup_inactive_states() # Remove inactive states

    # Search user by phone number in db
    user: User = db.query(User).filter(User.phone_number == phone_number).first()
    
    if not user:
        return "User not found"
    
    conversation_history = get_user_conversation_history(user.id, db)

    # message = ModelRequest.user_text_prompt(user_input)


    if phone_number not in user_states:

        user_timezone = dt_timezone.utc

        try:
            # Usar tu método del modelo
            tz = user.get_timezone_obj()
            now = datetime.now()
            offset = tz.utcoffset(now)
            user_timezone = dt_timezone(offset)
        except Exception as e:
            print(f"❌ Error con timezone {user.timezone}: {e}")
            user_timezone = dt_timezone.utc

        state = {
            "user_input": user_input,
            "user_id": user.id,
            "timezone": user_timezone,
            "name": user.name,
            "surname": user.surname,
            "phone_number": user.phone_number,
            "birth_date": user.birth_date,
            "email": user.email,
            "conversation_history": conversation_history,
            "agent_results": None,
            "reminder_results": None,
            "last_interaction": datetime.now(dt_timezone.utc),
        }
    else:
        # Actualizar el estado existente
        # new_message = ModelMessagesTypeAdapter.dump_json([
        #     ModelRequest.user_text_prompt(user_input)
        # ])
        state = user_states[phone_number]

        if "conversation_history" not in state:
            state["conversation_history"] = []
            
        current_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        }
        state["conversation_history"].append(current_message)
        state["user_input"] = user_input
        state["last_interaction"] = datetime.now(dt_timezone.utc)
        
    user_states[phone_number] = state

    config = {"configurable": {"thread_id": f"user_{user.id}"}}
    
    try:
        updated_state = await agent_graph.ainvoke(state, config=config)
        user_states[phone_number] = updated_state

        current_intent = updated_state.get("intent", "").lower()

        if current_intent == "reminder" and updated_state.get("reminder_results"):
            return updated_state["reminder_results"]
        
        # Si no hay reminder_results, devolver agent_results (aunque sea None)
        if current_intent == "general" and "agent_results" in updated_state:
            return updated_state["agent_results"]

        return None
                
    except Exception as e:
        print(f"Error en getting a response: {str(e)}")
        return None



# Función para limpiar estados inactivos
def cleanup_inactive_states():
    global user_states
    current_time = datetime.now(dt_timezone.utc)
    inactive_threshold = current_time - timedelta(minutes=30)
    
    user_states = {
        phone: state 
        for phone, state in user_states.items() 
        if state.get("last_interaction", datetime.min.replace(tzinfo=dt_timezone.utc)) > inactive_threshold
    }