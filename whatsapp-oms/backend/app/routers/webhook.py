from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from app.services.ai_agent import handle_message
from app.services.whatsapp import send_whatsapp

router = APIRouter(prefix="/webhook", tags=["webhook"])


async def _parse_inbound(request: Request) -> tuple[str, str]:
    """Supports both Twilio form-encoded posts and plain JSON for local tests."""
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        data = await request.json()
        return data.get("From", ""), data.get("Body", "")
    form = await request.form()
    return form.get("From", ""), form.get("Body", "")


@router.post("/whatsapp/{tenant_id}")
async def whatsapp_webhook(tenant_id: str, request: Request):
    """Single auto-routing webhook for every tenant. No new routes per branch."""
    from_number, body = await _parse_inbound(request)
    if not from_number or not body:
        return PlainTextResponse("", status_code=200)

    # Normalize phone (strip Twilio "whatsapp:" prefix for session key & storage).
    phone = from_number.replace("whatsapp:", "").strip()

    result = await handle_message(tenant_id, phone, body)
    await send_whatsapp(from_number, result["reply"])

    # Return JSON so local testing shows the reply; Twilio ignores body if 200.
    return JSONResponse({
        "tenant_id": tenant_id,
        "to": phone,
        "reply": result["reply"],
        "order_created": result["order_created"],
        "order_id": result["order_id"],
    })
