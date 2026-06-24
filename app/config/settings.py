import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    whatsapp_access_token: str
    whatsapp_phone_number_id: str
    whatsapp_verify_token: str
    gemini_api_key: str

    whatsapp_api_version: str = "v25.0"
    gemini_model: str = "gemini-2.5-flash"

    ai_fallback_message: str = (
        "Sorry, I am unable to respond right now.\nPlease try again later."
    )


settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
