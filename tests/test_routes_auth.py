import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
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

    from app.main import app
    return TestClient(app, follow_redirects=False)


def test_get_login_page(client):
    """GET /login returns the login page."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_get_register_page(client):
    """GET /register returns the registration page."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "Register" in response.text


def test_register_and_redirect(client):
    """POST /register creates user and redirects to home."""
    response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session_id" in response.cookies


def test_login_valid_credentials(client):
    """POST /login with valid credentials redirects to home."""
    client.post("/register", data={"email": "test@example.com", "password": "password123"})

    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "session_id" in response.cookies


def test_login_invalid_credentials(client):
    """POST /login with bad credentials returns login page with error."""
    response = client.post(
        "/login",
        data={"email": "bad@example.com", "password": "wrong"},
    )
    assert response.status_code == 200
    assert "Invalid" in response.text


def test_logout(client):
    """POST /logout clears session and redirects to login."""
    register_response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "password123"},
    )
    session_cookie = register_response.cookies.get("session_id")

    response = client.post("/logout", cookies={"session_id": session_cookie})
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_register_duplicate_email(client):
    """POST /register with existing email shows error."""
    client.post("/register", data={"email": "test@example.com", "password": "pass1"})
    response = client.post(
        "/register",
        data={"email": "test@example.com", "password": "pass2"},
    )
    assert response.status_code == 200
    assert "already registered" in response.text.lower()
