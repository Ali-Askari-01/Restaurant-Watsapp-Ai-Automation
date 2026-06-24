"""
Outbound WhatsApp sender. Uses Twilio if credentials are present, otherwise
mocks the send with a print() so the system works fully offline for the MVP.
"""
from app.config import settings

_client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client
        _client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    except Exception as e:  # pragma: no cover
        print(f"[whatsapp] Twilio init failed, falling back to mock: {e}")
        _client = None


def _normalize(number: str) -> str:
    number = number.strip()
    if not number.startswith("whatsapp:"):
        number = f"whatsapp:{number}"
    return number


async def send_whatsapp(to_number: str, body: str) -> None:
    """Send a WhatsApp message, or mock it if Twilio is not configured."""
    to = _normalize(to_number)
    if _client is None:
        print("\n────────── [MOCK WHATSAPP SEND] ──────────")
        print(f"TO:   {to}")
        print(f"FROM: {settings.TWILIO_WHATSAPP_FROM}")
        print(f"BODY:\n{body}")
        print("──────────────────────────────────────────\n")
        return
    try:
        _client.messages.create(
            from_=_normalize(settings.TWILIO_WHATSAPP_FROM),
            to=to,
            body=body,
        )
    except Exception as e:  # pragma: no cover
        print(f"[whatsapp] send failed: {e}")
