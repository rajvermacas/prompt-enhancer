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
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

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


def test_get_system_prompt_empty(client, workspace_id):
    """GET system-prompt returns empty content initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/system-prompt")

    assert response.status_code == 200
    assert response.json()["content"] == ""


def test_save_system_prompt(client, workspace_id):
    """PUT system-prompt saves and returns content."""
    payload = {"content": "Mention why other categories were not selected"}

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Mention why other categories were not selected"


def test_get_system_prompt_after_save(client, workspace_id):
    """GET system-prompt returns saved content."""
    client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json={"content": "Custom instructions here"},
    )

    response = client.get(f"/api/workspaces/{workspace_id}/prompts/system-prompt")

    assert response.status_code == 200
    assert response.json()["content"] == "Custom instructions here"


# --- Approval workflow tests for organization workspace ---


@pytest.fixture
def org_workspace_setup(tmp_path, monkeypatch):
    """Set up environment with organization workspace for approval testing."""
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

    # Create organization workspace with metadata
    org_dir = workspaces_dir / "organization"
    org_dir.mkdir()
    import json
    with open(org_dir / "metadata.json", "w") as f:
        json.dump({
            "id": "organization",
            "name": "Organization",
            "user_id": None,
            "created_at": "2024-01-01T00:00:00",
            "is_organization": True
        }, f)
    with open(org_dir / "category_definitions.json", "w") as f:
        json.dump({"categories": []}, f)
    with open(org_dir / "few_shot_examples.json", "w") as f:
        json.dump({"examples": []}, f)
    with open(org_dir / "system_prompt.json", "w") as f:
        json.dump({"content": ""}, f)
    (org_dir / "change_requests").mkdir()

    from app.dependencies import get_settings

    get_settings.cache_clear()

    from app.db import init_db

    init_db(str(tmp_path / "auth.db"))

    return tmp_path


@pytest.fixture
def user_client_for_org(org_workspace_setup):
    """Create test client with a regular user for org workspace testing."""
    from app.services.auth_service import AuthService
    from app.main import app

    auth = AuthService(str(org_workspace_setup / "auth.db"))
    # First user becomes APPROVER automatically, so register a dummy one first
    auth.register_user("first-approver@example.com", "password123")
    # Second user will be a regular USER
    user = auth.register_user("user@example.com", "password123")
    session = auth.create_session(user.id)

    test_client = TestClient(app)
    test_client.cookies.set("session_id", session.id)
    return test_client


@pytest.fixture
def approver_client_for_org(org_workspace_setup):
    """Create test client with an approver user for org workspace testing."""
    from app.models.auth import UserRole
    from app.services.auth_service import AuthService
    from app.services.user_service import UserService
    from app.main import app

    auth = AuthService(str(org_workspace_setup / "auth.db"))
    user = auth.register_user("approver@example.com", "password123")

    user_service = UserService(str(org_workspace_setup / "auth.db"))
    user_service.update_user_role(user.id, UserRole.APPROVER)

    session = auth.create_session(user.id)

    test_client = TestClient(app)
    test_client.cookies.set("session_id", session.id)
    return test_client


# --- Categories endpoint approval workflow tests ---


def test_save_org_categories_as_user_creates_change_request(user_client_for_org):
    """PUT org categories as regular user creates change request and returns 202."""
    categories = {
        "categories": [{"name": "Tech", "definition": "Technology news"}]
    }

    response = user_client_for_org.put(
        "/api/workspaces/organization/prompts/categories",
        json=categories,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["id"].startswith("cr-")
    assert data["prompt_type"] == "CATEGORY_DEFINITIONS"
    assert data["status"] == "PENDING"
    assert data["proposed_content"] == categories


def test_save_org_categories_as_approver_saves_directly(approver_client_for_org):
    """PUT org categories as approver saves directly and returns 200."""
    categories = {
        "categories": [{"name": "Tech", "definition": "Technology news"}]
    }

    response = approver_client_for_org.put(
        "/api/workspaces/organization/prompts/categories",
        json=categories,
    )

    assert response.status_code == 200
    assert response.json()["categories"] == categories["categories"]


def test_save_org_categories_duplicate_pending_returns_409(user_client_for_org):
    """PUT org categories with existing pending request returns 409."""
    categories = {"categories": [{"name": "Tech", "definition": "Technology news"}]}

    # First request should succeed with 202
    response1 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/categories",
        json=categories,
    )
    assert response1.status_code == 202

    # Second request should fail with 409
    response2 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/categories",
        json={"categories": [{"name": "Different", "definition": "Different def"}]},
    )
    assert response2.status_code == 409


# --- Few-shots endpoint approval workflow tests ---


def test_save_org_few_shots_as_user_creates_change_request(user_client_for_org):
    """PUT org few-shots as regular user creates change request and returns 202."""
    few_shots = {
        "examples": [
            {
                "id": "ex-001",
                "news_content": "Test news",
                "category": "Tech",
                "reasoning": "Test reasoning",
            }
        ]
    }

    response = user_client_for_org.put(
        "/api/workspaces/organization/prompts/few-shots",
        json=few_shots,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["id"].startswith("cr-")
    assert data["prompt_type"] == "FEW_SHOTS"
    assert data["status"] == "PENDING"
    assert data["proposed_content"] == few_shots


def test_save_org_few_shots_as_approver_saves_directly(approver_client_for_org):
    """PUT org few-shots as approver saves directly and returns 200."""
    few_shots = {
        "examples": [
            {
                "id": "ex-001",
                "news_content": "Test news",
                "category": "Tech",
                "reasoning": "Test reasoning",
            }
        ]
    }

    response = approver_client_for_org.put(
        "/api/workspaces/organization/prompts/few-shots",
        json=few_shots,
    )

    assert response.status_code == 200
    assert response.json()["examples"] == few_shots["examples"]


def test_save_org_few_shots_duplicate_pending_returns_409(user_client_for_org):
    """PUT org few-shots with existing pending request returns 409."""
    few_shots = {"examples": []}

    # First request should succeed with 202
    response1 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/few-shots",
        json=few_shots,
    )
    assert response1.status_code == 202

    # Second request should fail with 409
    response2 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/few-shots",
        json={"examples": [{"id": "ex-002", "news_content": "Other", "category": "X", "reasoning": "Y"}]},
    )
    assert response2.status_code == 409


# --- System-prompt endpoint approval workflow tests ---


def test_save_org_system_prompt_as_user_creates_change_request(user_client_for_org):
    """PUT org system-prompt as regular user creates change request and returns 202."""
    payload = {"content": "New system prompt content"}

    response = user_client_for_org.put(
        "/api/workspaces/organization/prompts/system-prompt",
        json=payload,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["id"].startswith("cr-")
    assert data["prompt_type"] == "SYSTEM_PROMPT"
    assert data["status"] == "PENDING"
    assert data["proposed_content"] == payload


def test_save_org_system_prompt_as_approver_saves_directly(approver_client_for_org):
    """PUT org system-prompt as approver saves directly and returns 200."""
    payload = {"content": "New system prompt content"}

    response = approver_client_for_org.put(
        "/api/workspaces/organization/prompts/system-prompt",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["content"] == payload["content"]


def test_save_org_system_prompt_duplicate_pending_returns_409(user_client_for_org):
    """PUT org system-prompt with existing pending request returns 409."""
    payload = {"content": "New system prompt"}

    # First request should succeed with 202
    response1 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/system-prompt",
        json=payload,
    )
    assert response1.status_code == 202

    # Second request should fail with 409
    response2 = user_client_for_org.put(
        "/api/workspaces/organization/prompts/system-prompt",
        json={"content": "Different content"},
    )
    assert response2.status_code == 409


# --- Personal workspace tests (should work as before) ---


def test_save_personal_categories_as_user_saves_directly(client, workspace_id):
    """PUT personal workspace categories as regular user saves directly."""
    categories = {"categories": [{"name": "Personal", "definition": "Personal category"}]}

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/categories",
        json=categories,
    )

    assert response.status_code == 200
    assert response.json()["categories"] == categories["categories"]


def test_save_personal_few_shots_as_user_saves_directly(client, workspace_id):
    """PUT personal workspace few-shots as regular user saves directly."""
    few_shots = {
        "examples": [
            {
                "id": "ex-001",
                "news_content": "Personal news",
                "category": "Personal",
                "reasoning": "Personal reasoning",
            }
        ]
    }

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/few-shots",
        json=few_shots,
    )

    assert response.status_code == 200
    assert response.json()["examples"] == few_shots["examples"]


def test_save_personal_system_prompt_as_user_saves_directly(client, workspace_id):
    """PUT personal workspace system-prompt as regular user saves directly."""
    payload = {"content": "Personal system prompt"}

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["content"] == payload["content"]
