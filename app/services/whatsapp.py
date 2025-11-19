import requests
from requests.adapters import HTTPAdapter, Retry
from app.config import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_ID


whatsapp_phone_id = WHATSAPP_PHONE_ID

class WhatsAppService:
    """
    WhatsApp API client with session reuse, retries and timeouts.
    """
    def __init__(
        self,
        access_token: str = WHATSAPP_ACCESS_TOKEN,
        phone_id: str = whatsapp_phone_id,
        api_version: str = "v18.0",
        timeout_sec: float = 10.0,
        max_retries: int = 3,
    ):
        self.access_token = access_token
        self.phone_id = phone_id
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.timeout_sec = timeout_sec

        # Reuse HTTP session with retries (idempotent POSTs are OK here)
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=50)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _normalize_phone(self, phone_number: str) -> str:
        # Remove leading '+' if present
        return phone_number[1:] if phone_number.startswith("+") else phone_number

    def send_text(self, phone_number: str, message: str) -> bool:
        """
        Send a simple WhatsApp text message.
        """
        to = self._normalize_phone(phone_number)
        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }
        resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout_sec)
        if resp.status_code == 200:
            return True
        print(f"[WhatsApp] Send error {resp.status_code}: {resp.text}")
        return False

    def mark_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        """
        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout_sec)
        return resp.status_code == 200

    # Envia recordatorio personalizado por WhatsApp
    def send_reminder(self, phone_number: str, message: str) -> bool:
        """
         🛈 Enviar recordatorio personalizado por WhatsApp
        """
        to = self._normalize_phone(phone_number)
        url = f"{self.base_url}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        resp = self.session.post(url, headers=self._headers(), json=payload, timeout=self.timeout_sec)
        if resp.status_code == 200:
            return True
        
        return False


_client = WhatsAppService()

def send_message(user_number: str, text: str) -> bool:
    """
    Convenience function that delegates to the reusable client.
    """
    return _client.send_text(user_number, text)



def send_whatsapp_message(user_number: str, text: str):
    """
      🛈 Enviar mensaje de basico de Whatsapp
    """

    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": user_number,
        "type": "text",
        "text": {
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Mensaje enviado correctamente.")
    else:
        print("❌ Error al enviar mensaje:", response.status_code, response.text)



def send_confirm_reminder_whatsapp(user_number: str, response: dict[str, any]):
    """
      🛈 Enviar mensaje de confirmación de recordatorio
    """

    if response is None:
        return None

    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    reminder_date = (
        response.reminder_date.strftime("%d/%m/%Y")
        if hasattr(response.reminder_date, "strftime")
        else str(response.reminder_date)
    )
    reminder_hour = (
        response.reminder_hour.strftime("%H:%M")
        if hasattr(response.reminder_hour, "strftime")
        else str(response.reminder_hour)
    )

    data = {
        "messaging_product": "whatsapp",
        "to": user_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
            "text": "¿Quieres confirmar el recordatorio *" + response.reminder_text + "* para que te lo recuerde  *" + reminder_date + "* a las *" + reminder_hour + "* ?"
            },
            "action": {
                "buttons": [
                    {
                    "type": "reply",
                    "reply": {
                        "id": "accept_reminder",
                        "title": "✅ Aceptar"
                    }
                    },
                    {
                    "type": "reply",
                    "reply": {
                        "id": "reject_reminder",
                        "title": "❌ Rechazar"
                    }
                    }
                ]
            }
        }
    }

    res = requests.post(url, headers=headers, json=data)

    if res.status_code != 200:
        print("❌ Error marcando como leído:", res.status_code, res.text)



def mark_whatsapp_message_as_read(message_id: str):
    """
      🛈 Marcar los mensajes del usuario como leidos en WHATSAPP
    """

    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}/messages"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    
    data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    
    r = requests.post(url, headers=headers, json=data)
    
    if r.status_code != 200:
        print("❌ Error marcando como leído:", r.status_code, r.text)