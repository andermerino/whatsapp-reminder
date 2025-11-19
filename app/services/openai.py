from app.config import OPENAI_API_KEY
from openai import OpenAI
from datetime import datetime


    
def crear_mensaje_personalizado(reminder_text: str, reminder_date: str, reminder_hour: str, user_name: str):
    '''
        Crea mensaje personalizado para enviar el recordatorio
    '''
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model="gpt-4o",
        instructions=f"Create a personalized reminder message for the user based on the reminder text, date and hour; if the date is the same as  {today_date()}, you must say that it is today, and the same with tomorrow etc. Be concise and to the point, make a short message. Speak like is your lifelong friend, call him by his name. You must speak in spanish from spain.",
        input=f"Reminder me, {user_name}, that you need to {reminder_text} on {reminder_date} at {reminder_hour}",
    )
    return response.output_text



def today_date():
    return datetime.now().strftime("%A %d/%m/%Y")

