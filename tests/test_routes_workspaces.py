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

    # Create required files
    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.main import app

    return TestClient(app)


def test_create_workspace(client):
    """POST /api/workspaces creates a new workspace."""
    response = client.post("/api/workspaces", json={"name": "Test Workspace"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workspace"
    assert "id" in data


def test_list_workspaces(client):
    """GET /api/workspaces returns all workspaces."""
    client.post("/api/workspaces", json={"name": "WS1"})
    client.post("/api/workspaces", json={"name": "WS2"})

    response = client.get("/api/workspaces")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_delete_workspace(client):
    """DELETE /api/workspaces/{id} removes workspace."""
    create_response = client.post("/api/workspaces", json={"name": "To Delete"})
    workspace_id = create_response.json()["id"]

    response = client.delete(f"/api/workspaces/{workspace_id}")

    assert response.status_code == 204

    list_response = client.get("/api/workspaces")
    assert len(list_response.json()) == 0
