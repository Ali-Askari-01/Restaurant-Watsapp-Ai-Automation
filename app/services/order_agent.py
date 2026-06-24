import json
import logging
import re

import google.generativeai as genai

from app.config.settings import settings
from app.data.restaurants import format_menus_for_prompt
from app.services.session_service import get_session, reset_session, save_confirmed_order

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)

ORDER_JSON_PATTERN = re.compile(
    r"\[ORDER_JSON\]\s*(\{.*?\})\s*\[/ORDER_JSON\]",
    re.DOTALL,
)

SYSTEM_PROMPT = f"""You are a friendly WhatsApp ordering assistant for a restaurant management system.

You serve TWO restaurants only:
1. Kababjees — Pakistani BBQ & biryani
2. KFC — Fried chicken & fast food

MENUS (prices in PKR):
{format_menus_for_prompt()}

ORDER FLOW — follow these steps in order:
1. Greet the customer and ask which restaurant they want: Kababjees or KFC.
2. Once they choose, show that restaurant's full menu with item numbers and prices.
3. Take their order — ask what items and quantities they want. Help them choose from the menu.
4. Ask for their full name and delivery address.
5. Show a clear order summary: restaurant, items with quantities, line totals, and grand total in PKR.
6. Ask them to reply YES to confirm or NO to change the order.
7. When they confirm with YES, thank them and say the order is placed. Estimate delivery 45-60 minutes.

RULES:
- Only offer items from the selected restaurant's menu. Do not invent items or prices.
- Calculate totals correctly using the menu prices.
- Keep replies concise and WhatsApp-friendly (short paragraphs, use line breaks).
- Be polite and professional.
- If the customer says "menu", show the menu again for their chosen restaurant.
- If the customer says "reset" or "start over", greet them fresh and ask which restaurant again.
- If they want to switch restaurants before confirming, allow it and show the new menu.
- Currency is always PKR (Rs).
- Do not use emojis.

WHEN ORDER IS CONFIRMED (customer said YES after seeing summary), append this block at the very end of your message (customer must not see awkward formatting — keep the thank-you message natural above it):

[ORDER_JSON]
{{"restaurant": "kababjees or kfc", "customer_name": "...", "address": "...", "items": [{{"item": "...", "quantity": 1, "unit_price_pkr": 0, "line_total_pkr": 0}}], "total_pkr": 0}}
[/ORDER_JSON]
"""


def _build_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(
        settings.gemini_model,
        system_instruction=SYSTEM_PROMPT,
    )


def _strip_order_json(text: str) -> tuple[str, dict | None]:
    match = ORDER_JSON_PATTERN.search(text)
    if not match:
        return text.strip(), None

    customer_text = ORDER_JSON_PATTERN.sub("", text).strip()
    try:
        order = json.loads(match.group(1))
        return customer_text, order
    except json.JSONDecodeError:
        logger.exception("Failed to parse order JSON from AI response")
        return customer_text, None


def process_order_message(phone: str, user_message: str) -> str:
    normalized = user_message.strip().lower()
    if normalized in {"reset", "start over", "restart", "new order"}:
        reset_session(phone)

    session = get_session(phone)

    try:
        model = _build_model()
        chat = model.start_chat(history=session.history)
        response = chat.send_message(user_message)
        raw_text = (response.text or "").strip()

        if not raw_text:
            return settings.ai_fallback_message

        session.history = chat.history[-20:]

        customer_reply, order = _strip_order_json(raw_text)
        if order:
            order["phone"] = phone
            save_confirmed_order(phone, order)
            logger.info("Order confirmed for %s: %s", phone, json.dumps(order))

        return customer_reply or settings.ai_fallback_message

    except Exception:
        logger.exception("Order agent failed for %s", phone)
        return settings.ai_fallback_message
