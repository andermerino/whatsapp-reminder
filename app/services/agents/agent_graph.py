from datetime import timezone
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from typing_extensions import TypedDict
from langgraph.types import interrupt
from datetime import date


# Import the agents
from app.services.agents.agent import agent, AgentDeps
from app.services.agents.reminder_agent import reminder_agent, ReminderDeps
from app.services.agents.classifier_agent import classifier_agent, IntentDeps


# logfire.configure(send_to_logfire='never')


# Define the state for the graph
class AgentState(TypedDict):
    user_input: str
    conversation_history: List[Dict[str, Any]]

    # Dependencies
    user_id: int
    timezone: timezone
    name: str
    surname: str
    phone_number: str
    email: str
    birth_date: date

    # Result from each agent
    agent_results: str
    reminder_results: str
    intent: str



# ----- Node: Agent -----
async def agent_node(state: AgentState) -> Dict[str, Any]:

    print("\n🤖 AGENT INICIADO")

    result = await agent.run(
        state["user_input"],
        deps = AgentDeps(
            user_id=state["user_id"],
            name=state["name"],
            surname=state["surname"],
            phone_number=state["phone_number"],
            email=state["email"],
            birth_date=state["birth_date"],
            conversation_history=state["conversation_history"]
        )
    )
    
    output = result.output
    print(f"🤖 AGENT OUTPUT: {output}")

    return { 
        "agent_results": output,
        "is_reminder": output.is_reminder,
        "intent": "general"
    }



# ----- Node: Reminder agent -----
async def get_reminder_node(state: AgentState) -> Dict[str, Any]:
    print("\n📋 REMINDER INICIADO")


    result = await reminder_agent.run(
        state["user_input"], 
        deps=ReminderDeps(
            user_id=state["user_id"],
            timezone=state["timezone"],
            conversation_history=state["conversation_history"]
        ),
    )
    

    output = result.output
    print(f"📋 REMINDER OUTPUT: {output}")

    return { "reminder_results": output}



# ----- Node: Get next user message -----
async def get_next_user_message_node(state: AgentState) -> Dict[str, Any]:

    user_input = interrupt({})
    user_input = state.get("user_input", "").strip()
    
    if not user_input:
        return {
            "error": "No se detectó ningún mensaje",
            "suggested_responses": ["¿Podrías repetirlo?", "No te he entendido, ¿podrías decirlo de otra forma?"]
        }
    
    if len(user_input) > 500:
        return {
            "error": "Mensaje demasiado largo",
            "suggested_responses": ["Voy a resumir tu mensaje..."]
        }
    
    return {
        **state,  # Mantener el estado actual
        "user_input": user_input
    }
    


# ----- Node: Intent classifier agent  -----
async def get_intent_classifier_node(state: AgentState) -> Dict[str, Any]:
    print("\n🤖 INTENT CLASSIFIER INICIADO")

    result = await classifier_agent.run(
        state["user_input"],
        deps=IntentDeps(
            user_id= state["user_id"],
            conversation_history= state["conversation_history"]
        ),
    )

    output = result.output
    print(f"🤖 INTENT CLASSIFIER OUTPUT: {output}")

    return { "intent": output.intent}



# ----- Functions for the graph -----
def route_task(state: AgentState):
    if state["intent"] == "reminder":
        return "get_reminder"
    elif state["intent"] == "general":
        return "agent"
    elif state["intent"] == "unknown":
        return END



def is_reminder_complete(state: AgentState):
    reminder = state.get("reminder_results")
    if reminder and hasattr(reminder, "reminder_is_complete") and reminder.reminder_is_complete:
        return END
    else:
        return "get_next_user_message" 



# Build the graph
def build_agent_graph():
    """ Build and return the agent graph """

    # Create the graph using the AgentState
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("get_reminder", get_reminder_node)
    graph.add_node("get_next_user_message", get_next_user_message_node)
    graph.add_node("intent_classifier", get_intent_classifier_node)


    graph.set_entry_point("intent_classifier")

    graph.add_conditional_edges(
        "intent_classifier",
        route_task,
        ["get_reminder", "agent", END ]
    )

    graph.add_conditional_edges(
        "get_reminder",
        is_reminder_complete,
        ["get_next_user_message", END ]
    )

    graph.add_edge("agent", "get_next_user_message")
    graph.add_edge("get_next_user_message", "intent_classifier")



    # Compile the graph
    memory = MemorySaver()
    compiled_graph = graph.compile(checkpointer=memory)

    return compiled_graph



# ----- Export the graph -----
try:
    agent_graph = build_agent_graph()
except Exception as e:
    print(f"Error building agent graph: {e}")
    raise