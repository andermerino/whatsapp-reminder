# WhatsApp Reminder

Sistema de recordatorios por WhatsApp que utiliza inteligencia artificial para entender mensajes naturales y crear recordatorios programados automáticamente.

## ¿Cómo funciona?

El sistema funciona mediante un webhook de WhatsApp que recibe los mensajes de los usuarios. Cuando un usuario envía un mensaje:

1. **Procesamiento con IA**: El mensaje es analizado por agentes de IA que identifican si contiene información de un recordatorio
2. **Extracción de datos**: Si se detecta un recordatorio, se extraen la fecha, hora y descripción
3. **Confirmación**: Se envía un mensaje de confirmación al usuario con botones para aceptar o rechazar el recordatorio
4. **Programación**: Una vez confirmado, el recordatorio se guarda en la base de datos y se programa para ser enviado automáticamente
5. **Envío automático**: Celery Beat verifica periódicamente los recordatorios pendientes y los envía por WhatsApp en el momento programado

El sistema también mantiene un historial de conversaciones y memorias de los usuarios para proporcionar respuestas más contextualizadas.

## Arquitectura

La aplicación está construida con:

- **FastAPI**: API REST para recibir webhooks de WhatsApp y gestionar usuarios
- **PostgreSQL**: Base de datos para almacenar usuarios, recordatorios, mensajes y memorias
- **Redis**: Broker de mensajes para Celery
- **Celery**: Sistema de tareas asíncronas
  - **Celery Worker**: Procesa las tareas de envío de mensajes
  - **Celery Beat**: Programa y ejecuta los recordatorios
- **OpenAI**: Modelos de IA para procesar mensajes y extraer información
- **WhatsApp Business API**: Integración para enviar y recibir mensajes

## Variables de Entorno

Para que la aplicación funcione correctamente, necesitas configurar las siguientes variables de entorno en un archivo `.env`:

### Base de Datos
- `DATABASE_LOCAL_URL`: URL de conexión a PostgreSQL (ej: `postgresql://user:password@localhost:5432/dbname`)

### WhatsApp Business API
- `WHATSAPP_ACCESS_TOKEN`: Token de acceso de la API de WhatsApp
- `WHATSAPP_PHONE_ID`: ID del número de teléfono de WhatsApp Business

### OpenAI
- `OPENAI_API_KEY`: Clave de API de OpenAI para los modelos de IA
- `LLM_API_KEY`: (Opcional) Clave alternativa para los modelos, si no se proporciona usa `OPENAI_API_KEY`

### Seguridad
- `FERNET_KEY`: Clave de cifrado para datos sensibles (mensajes encriptados en la base de datos)

### Celery
- `CELERY_BROKER_URL`: URL de Redis como broker (ej: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND`: URL de Redis como backend de resultados (ej: `redis://localhost:6379/0`)

## Endpoints Principales

- `POST /whatsapp/`: Webhook para recibir mensajes de WhatsApp
- `GET /whatsapp/`: Verificación del webhook de WhatsApp
- Otros endpoints para gestión de usuarios, recordatorios y mensajes

## Requisitos

- Python >= 3.12
- PostgreSQL (para instalación local)
- Redis (para instalación local)
- Docker y Docker Compose (opcional, para instalación con Docker)
- ngrok (para instalación local, necesario para exponer el servidor a internet)
- Cuenta de WhatsApp Business API
- Cuenta de OpenAI con API key


## Instalación Local

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd whatsapp-reminder
   ```

2. **Instalar dependencias**:
   
   Si usas `uv` (recomendado):
   ```bash
   uv sync
   ```
   
   O si prefieres usar `pip`:
   ```bash
   pip install -e .
   ```

3. **Configurar variables de entorno**:
   
   Crea un archivo `.env` en la raíz del proyecto con las variables necesarias (ver sección [Variables de Entorno](#variables-de-entorno))

4. **Configurar base de datos**:
   
   Asegúrate de tener PostgreSQL y Redis ejecutándose localmente, o configura las URLs de conexión en tu archivo `.env`.

5. **Inicializar la base de datos**:
   ```bash
   # Ejecuta las migraciones o scripts de inicialización si los hay
   ```

6. **Ejecutar la aplicación**:
   
   En terminales separadas:
   ```bash
   # Terminal 1: FastAPI
   uvicorn app.main:app --reload
   
   # Terminal 2: Celery Worker
   celery -A app.celery_app worker --loglevel=info
   
   # Terminal 3: Celery Beat
   celery -A app.celery_app beat --loglevel=info
   ```

7. **Configurar ngrok para webhooks de WhatsApp**:
   
   Para que WhatsApp pueda enviar webhooks a tu servidor local, necesitas exponerlo a internet usando ngrok:
   
   a. **Instalar ngrok**:
      - Descarga [ngrok.com](https://ngrok.com/download)
   
   b. **Autenticarse en ngrok** (si es la primera vez):
      ```bash
      ngrok config add-authtoken <tu-token-de-ngrok>
      ```
      Puedes obtener tu token registrándote en [ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
   
   c. **Exponer el servidor local**:
      ```bash
      ngrok http 8000
      ```
      Esto creará un túnel público (ej: `https://abc123.ngrok.io`) que apunta a tu servidor local en el puerto 8000.
   
   d. **Configurar el webhook en WhatsApp Business API**:
      - Copia la URL de ngrok (ej: `https://abc123.ngrok.io`)
      - Configura el webhook en tu cuenta de WhatsApp Business API apuntando a:
        ```
        https://abc123.ngrok.io/whatsapp/
        ```
      - El endpoint de verificación será: `https://abc123.ngrok.io/whatsapp/` (GET)
      - El endpoint de webhook será: `https://abc123.ngrok.io/whatsapp/` (POST)
   
   **Nota importante**: La URL de ngrok cambia cada vez que reinicias ngrok.

**Nota**: También existe la disponibilidad de desplegarlo con Docker.
