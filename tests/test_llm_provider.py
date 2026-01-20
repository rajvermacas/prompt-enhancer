import pytest


def test_get_openrouter_llm(monkeypatch):
    """LLMProvider returns OpenRouter LLM when configured."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.agents.llm_provider import get_llm
    from app.config import Settings

    settings = Settings()
    llm = get_llm(settings)

    assert llm is not None


def test_get_llm_missing_api_key(monkeypatch):
    """LLMProvider raises error when API key missing."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.agents.llm_provider import LLMConfigurationError, get_llm
    from app.config import Settings

    settings = Settings()

    with pytest.raises(LLMConfigurationError):
        get_llm(settings)
