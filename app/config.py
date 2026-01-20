from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM Provider
    llm_provider: Literal["openrouter", "azure", "gemini"]

    # OpenRouter
    openrouter_api_key: str | None = None
    openrouter_model: str = "anthropic/claude-3.5-sonnet"

    # Azure OpenAI
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None

    # Gemini
    google_api_key: str | None = None
    gemini_model: str = "gemini-1.5-pro"

    # Data paths
    news_csv_path: str
    workspaces_path: str
    system_prompt_path: str

    @field_validator("llm_provider", mode="before")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        if v not in ("openrouter", "azure", "gemini"):
            raise ValueError(f"Invalid LLM provider: {v}")
        return v
