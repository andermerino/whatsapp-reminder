from fastapi import FastAPI
from app.database import Base, engine
from app.routers import user, message, reminder, memory, whatsapp

app = FastAPI()

# Routers
app.include_router(user.router)
app.include_router(message.router)
app.include_router(reminder.router)
app.include_router(memory.router)
app.include_router(whatsapp.router)

Base.metadata.create_all(bind=engine)

@app.get("/")


def read_root():
    return {"message": "¡Hello this app create reminders for you with whatsapp!"}