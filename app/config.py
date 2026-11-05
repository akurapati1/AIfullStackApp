from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "echo"  # "echo" | "openai-compatible"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_model: str = "llama-3.1-8b-instant"
    llm_timeout_seconds: float = 60.0
    system_prompt: str = "You are a concise, helpful assistant."
    database_path: str = "data/chat.db"
    history_window: int = 20  # number of prior messages sent to the model


@lru_cache
def get_settings() -> Settings:
    return Settings()
