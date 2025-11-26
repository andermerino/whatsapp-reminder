import os
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_LOCAL_URL")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FERNET_KEY = os.getenv("FERNET_KEY")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")


# Agents openai model
def get_model():
    api_key = os.getenv('LLM_API_KEY', OPENAI_API_KEY)

    return OpenAIModel(
        'gpt-4o',
        provider=OpenAIProvider(api_key=api_key)
    )

def get_classifier_model():
    api_key = os.getenv('LLM_API_KEY', OPENAI_API_KEY)

    return OpenAIModel(
        'gpt-3.5-turbo-0125',
        provider=OpenAIProvider(api_key=api_key)
    )