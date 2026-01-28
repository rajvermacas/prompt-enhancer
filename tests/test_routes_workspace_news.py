import csv
import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with temporary data directories."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    # Create default news CSV
    with open(tmp_path / "news.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        writer.writerow({"id": "default-1", "headline": "Default News", "content": "Content"})

    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.main import app
    return TestClient(app)


@pytest.fixture
def workspace_id(client):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json={"name": "Test WS"})
    return response.json()["id"]


def test_add_single_article(client, workspace_id):
    """POST /api/workspaces/{id}/news adds a single article."""
    response = client.post(
        f"/api/workspaces/{workspace_id}/news",
        json={"headline": "New Article", "content": "Article content", "date": "2026-01-15"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["headline"] == "New Article"
    assert data["content"] == "Article content"
    assert data["date"] == "2026-01-15"
    assert "id" in data


def test_upload_csv(client, workspace_id):
    """POST /api/workspaces/{id}/news/upload-csv uploads CSV file."""
    csv_content = "id,headline,content,date\n1,CSV News,CSV Content,2026-01-01"
    files = {"file": ("news.csv", io.BytesIO(csv_content.encode()), "text/csv")}

    response = client.post(
        f"/api/workspaces/{workspace_id}/news/upload-csv",
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_get_workspace_news(client, workspace_id):
    """GET /api/workspaces/{id}/news returns news for workspace."""
    response = client.get(f"/api/workspaces/{workspace_id}/news?page=1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert data["total"] == 1  # Default news


def test_set_news_source(client, workspace_id):
    """PUT /api/workspaces/{id}/news-source updates preference."""
    response = client.put(
        f"/api/workspaces/{workspace_id}/news-source",
        json={"news_source": "replace"}
    )

    assert response.status_code == 200
    assert response.json()["news_source"] == "replace"


def test_get_news_source(client, workspace_id):
    """GET /api/workspaces/{id}/news-source returns current preference."""
    response = client.get(f"/api/workspaces/{workspace_id}/news-source")

    assert response.status_code == 200
    assert response.json()["news_source"] == "merge"
