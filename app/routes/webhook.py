import logging

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from app.config.settings import settings
from app.services.order_agent import process_order_message
from app.services.whatsapp_service import send_text_message

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_text_message(payload: dict[str, Any]) -> dict[str, str] | None:
    try:
        entry = payload.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        if message.get("type") != "text":
            return None

        text_body = message.get("text", {}).get("body", "").strip()
        phone_number = message.get("from", "").strip()

        if not phone_number or not text_body:
            return None

        return {"phone_number": phone_number, "message": text_body}
    except (IndexError, KeyError, TypeError, AttributeError):
        logger.exception("Failed to parse WhatsApp webhook payload")
        return None


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.info("Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("Webhook verification failed: invalid token or mode")
    raise HTTPException(status_code=403, detail="Forbidden")


async def _handle_incoming_message(phone_number: str, user_message: str) -> None:
    logger.info("Processing message from %s: %s", phone_number, user_message)
    ai_response = process_order_message(phone_number, user_message)
    logger.info("AI response generated for %s", phone_number)

    sent = await send_text_message(phone_number, ai_response)
    if not sent:
        logger.error(
            "Failed to send reply to %s — check WhatsApp access token in .env",
            phone_number,
        )
    else:
        logger.info("Reply sent successfully to %s", phone_number)


@router.post("/webhook")
async def receive_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    try:
        payload = await request.json()
    except Exception:
        logger.exception("Invalid webhook payload")
        return {"status": "ok"}

    message_data = extract_text_message(payload)
    if not message_data:
        return {"status": "ok"}

    background_tasks.add_task(
        _handle_incoming_message,
        message_data["phone_number"],
        message_data["message"],
    )
    return {"status": "ok"}
