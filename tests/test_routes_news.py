import csv

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with sample news data."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    # Create news CSV with sample data
    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        for i in range(25):
            writer.writerow({
                "id": f"news-{i:03d}",
                "headline": f"Headline {i}",
                "content": f"Content {i}",
            })

    monkeypatch.setenv("NEWS_CSV_PATH", str(csv_path))
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.db import init_db

    init_db(str(tmp_path / "auth.db"))

    from app.services.auth_service import AuthService

    auth = AuthService(str(tmp_path / "auth.db"))
    user = auth.register_user("test@example.com", "password123")
    session = auth.create_session(user.id)

    from app.main import app

    client = TestClient(app)
    client.cookies.set("session_id", session.id)
    return client


def test_get_news_paginated(client):
    """GET /api/news returns paginated news."""
    response = client.get("/api/news?page=1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data["articles"]) == 10
    assert data["total"] == 25
    assert data["page"] == 1


def test_get_news_second_page(client):
    """GET /api/news returns correct page."""
    response = client.get("/api/news?page=2&limit=10")

    data = response.json()
    assert data["articles"][0]["id"] == "news-010"
