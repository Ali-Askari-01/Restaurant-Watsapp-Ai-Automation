import logging

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

WHATSAPP_MESSAGES_URL = (
    f"https://graph.facebook.com/{settings.whatsapp_api_version}"
    f"/{settings.whatsapp_phone_number_id}/messages"
)


async def send_text_message(to: str, message: str) -> bool:
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WHATSAPP_MESSAGES_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError:
        logger.exception(
            "WhatsApp API error: %s",
            response.text if "response" in locals() else "unknown",
        )
        return False
    except Exception:
        logger.exception("Failed to send WhatsApp message")
        return False
