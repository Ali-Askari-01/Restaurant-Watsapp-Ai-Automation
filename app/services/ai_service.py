import logging
from typing import Any

import google.generativeai as genai

from app.config.settings import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel(settings.gemini_model)


def generate_response(user_message: str) -> str:
    try:
        response = _model.generate_content(user_message)
        text = response.text
        if text and text.strip():
            return text.strip()
        logger.error("Gemini returned empty response")
        return settings.ai_fallback_message
    except Exception:
        logger.exception("Gemini API request failed")
        return settings.ai_fallback_message
