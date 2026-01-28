import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


def test_get_current_user_valid_session(tmp_path, monkeypatch):
    """get_current_user returns user when valid session cookie exists."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    db_path = str(tmp_path / "auth.db")
    init_db(db_path)

    from app.services.auth_service import AuthService
    auth = AuthService(db_path)
    user = auth.register_user("test@example.com", "password123")
    session = auth.create_session(user.id)

    from app.dependencies import get_current_user
    request = MagicMock()
    request.cookies = {"session_id": session.id}

    result = get_current_user(request)
    assert result.email == "test@example.com"


def test_get_current_user_no_cookie_raises(tmp_path, monkeypatch):
    """get_current_user raises HTTPException when no session cookie."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    init_db(str(tmp_path / "auth.db"))

    from app.dependencies import get_current_user
    request = MagicMock()
    request.cookies = {}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request)
    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_session_raises(tmp_path, monkeypatch):
    """get_current_user raises HTTPException for invalid session ID."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.db import init_db
    init_db(str(tmp_path / "auth.db"))

    from app.dependencies import get_current_user
    request = MagicMock()
    request.cookies = {"session_id": "invalid-session-id"}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request)
    assert exc_info.value.status_code == 401
