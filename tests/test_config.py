import pytest
from pydantic import ValidationError


def test_config_requires_llm_provider(monkeypatch):
    """Config must have LLM_PROVIDER set."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")
    monkeypatch.setenv("AUTH_DB_PATH", "./data/auth.db")

    from app.config import Settings
    with pytest.raises(ValidationError):
        Settings()


def test_config_loads_openrouter_settings(monkeypatch):
    """Config loads OpenRouter settings when provider is openrouter."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")
    monkeypatch.setenv("AUTH_DB_PATH", "./data/auth.db")

    from app.config import Settings
    settings = Settings()

    assert settings.llm_provider == "openrouter"
    assert settings.openrouter_api_key == "test-key"
    assert settings.openrouter_model == "anthropic/claude-3.5-sonnet"
