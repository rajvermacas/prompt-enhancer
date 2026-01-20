import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with workspace."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.main import app

    return TestClient(app)


@pytest.fixture
def workspace_id(client):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json={"name": "Test"})
    return response.json()["id"]


def test_get_categories_empty(client, workspace_id):
    """GET categories returns empty list initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/categories")

    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_save_categories(client, workspace_id):
    """PUT categories saves and returns categories."""
    categories = {
        "categories": [
            {"name": "Cat1", "definition": "Definition 1"}
        ]
    }

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/categories",
        json=categories,
    )

    assert response.status_code == 200
    assert len(response.json()["categories"]) == 1


def test_get_few_shots_empty(client, workspace_id):
    """GET few-shots returns empty list initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/few-shots")

    assert response.status_code == 200
    assert response.json()["examples"] == []


def test_save_few_shots(client, workspace_id):
    """PUT few-shots saves and returns examples."""
    few_shots = {
        "examples": [
            {
                "id": "ex-001",
                "news_content": "Test news",
                "category": "Cat1",
                "reasoning": "Test reasoning",
            }
        ]
    }

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/few-shots",
        json=few_shots,
    )

    assert response.status_code == 200
    assert len(response.json()["examples"]) == 1
