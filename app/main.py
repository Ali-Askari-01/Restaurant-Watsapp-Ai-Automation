import logging

import httpx
from fastapi import FastAPI

from app.config.settings import settings
from app.routes.webhook import router as webhook_router

logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp AI Agent MVP")

app.include_router(webhook_router)


async def check_whatsapp_token() -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://graph.facebook.com/v25.0/me",
                params={"access_token": settings.whatsapp_access_token},
            )
            if response.is_success:
                logger.info("WhatsApp access token is valid")
                return True
            error = response.json().get("error", {})
            logger.error(
                "WhatsApp access token INVALID: %s — Generate a new token in Meta Developer "
                "Console > WhatsApp > API Setup and update .env",
                error.get("message", response.text),
            )
            return False
    except Exception:
        logger.exception("Could not verify WhatsApp access token")
        return False


@app.on_event("startup")
async def startup_checks() -> None:
    await check_whatsapp_token()


@app.get("/")
async def health_check() -> dict[str, str | bool]:
    token_ok = await check_whatsapp_token()
    return {
        "status": "running",
        "whatsapp_token_valid": token_ok,
    }
