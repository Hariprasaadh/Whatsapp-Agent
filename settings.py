from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    RAPIDAPI_KEY: Optional[str] = None

    QDRANT_API_KEY: Optional[str] = None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: Optional[str] = None

    TEXT_MODEL_NAME: str = "llama-3.1-8b-instant"
    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    ITT_MODEL_NAME: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "data/memory.db"

    GENERATED_AUDIO_DIR: str = "generated/audio"
    GENERATED_IMAGE_DIR: str = "generated/image"

    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None


settings = Settings()