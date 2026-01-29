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


# --- Copy From Organization Endpoint Tests ---


@pytest.fixture
def org_workspace_with_prompts(tmp_path, monkeypatch):
    """Set up environment with organization workspace containing prompts."""
    import json

    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    workspaces_dir = tmp_path / "workspaces"
    workspaces_dir.mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    # Create organization workspace with prompts
    org_dir = workspaces_dir / "organization"
    org_dir.mkdir()
    with open(org_dir / "metadata.json", "w") as f:
        json.dump({
            "id": "organization",
            "name": "Organization",
            "user_id": None,
            "created_at": "2024-01-01T00:00:00",
            "is_organization": True
        }, f)
    with open(org_dir / "category_definitions.json", "w") as f:
        json.dump({
            "categories": [
                {"name": "Tech", "definition": "Technology news"},
                {"name": "Finance", "definition": "Financial news"}
            ]
        }, f)
    with open(org_dir / "few_shot_examples.json", "w") as f:
        json.dump({
            "examples": [
                {
                    "id": "org-ex-001",
                    "news_content": "Apple releases new iPhone",
                    "category": "Tech",
                    "reasoning": "This is tech news about Apple"
                }
            ]
        }, f)
    with open(org_dir / "system_prompt.json", "w") as f:
        json.dump({"content": "Organization system prompt"}, f)
    (org_dir / "change_requests").mkdir()

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.db import init_db

    init_db(str(tmp_path / "auth.db"))

    return tmp_path


@pytest.fixture
def user_client_with_org(org_workspace_with_prompts):
    """Create test client with a user for copy-from-org testing."""
    from app.services.auth_service import AuthService
    from app.main import app

    auth = AuthService(str(org_workspace_with_prompts / "auth.db"))
    user = auth.register_user("user@example.com", "password123")
    session = auth.create_session(user.id)

    test_client = TestClient(app)
    test_client.cookies.set("session_id", session.id)
    test_client.user_id = user.id
    return test_client


def test_copy_from_organization(user_client_with_org):
    """POST /api/workspaces/{id}/copy-from-organization copies org prompts."""
    # Create a user workspace
    create_response = user_client_with_org.post(
        "/api/workspaces", json={"name": "My Workspace"}
    )
    assert create_response.status_code == 201
    workspace_id = create_response.json()["id"]

    # Verify workspace starts empty
    categories_before = user_client_with_org.get(
        f"/api/workspaces/{workspace_id}/prompts/categories"
    )
    assert categories_before.json()["categories"] == []

    # Copy from organization
    copy_response = user_client_with_org.post(
        f"/api/workspaces/{workspace_id}/copy-from-organization"
    )
    assert copy_response.status_code == 200
    assert copy_response.json()["success"] is True

    # Verify categories were copied
    categories_after = user_client_with_org.get(
        f"/api/workspaces/{workspace_id}/prompts/categories"
    )
    assert len(categories_after.json()["categories"]) == 2
    assert categories_after.json()["categories"][0]["name"] == "Tech"
    assert categories_after.json()["categories"][1]["name"] == "Finance"

    # Verify few-shots were copied
    few_shots_after = user_client_with_org.get(
        f"/api/workspaces/{workspace_id}/prompts/few-shots"
    )
    assert len(few_shots_after.json()["examples"]) == 1
    assert few_shots_after.json()["examples"][0]["id"] == "org-ex-001"

    # Verify system prompt was copied
    system_prompt_after = user_client_with_org.get(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt"
    )
    assert system_prompt_after.json()["content"] == "Organization system prompt"


def test_copy_from_organization_to_other_user_workspace_forbidden(
    org_workspace_with_prompts,
):
    """Cannot copy to workspace you don't own."""
    from app.services.auth_service import AuthService
    from app.main import app

    auth = AuthService(str(org_workspace_with_prompts / "auth.db"))

    # Create first user and their workspace
    user1 = auth.register_user("user1@example.com", "password123")
    session1 = auth.create_session(user1.id)
    client1 = TestClient(app)
    client1.cookies.set("session_id", session1.id)

    create_response = client1.post("/api/workspaces", json={"name": "User1 Workspace"})
    user1_workspace_id = create_response.json()["id"]

    # Create second user
    user2 = auth.register_user("user2@example.com", "password123")
    session2 = auth.create_session(user2.id)
    client2 = TestClient(app)
    client2.cookies.set("session_id", session2.id)

    # User2 tries to copy to User1's workspace - should fail
    copy_response = client2.post(
        f"/api/workspaces/{user1_workspace_id}/copy-from-organization"
    )
    assert copy_response.status_code == 403
    assert "Cannot copy to workspace you don't own" in copy_response.json()["detail"]


def test_copy_to_organization_workspace_fails(user_client_with_org):
    """Cannot copy to organization workspace itself."""
    copy_response = user_client_with_org.post(
        "/api/workspaces/organization/copy-from-organization"
    )
    assert copy_response.status_code == 400
    assert "Cannot copy to organization workspace" in copy_response.json()["detail"]
