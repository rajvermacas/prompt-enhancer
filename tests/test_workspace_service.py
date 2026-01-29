import pytest


@pytest.fixture
def workspaces_dir(tmp_path):
    """Create a temporary workspaces directory."""
    ws_dir = tmp_path / "workspaces"
    ws_dir.mkdir()
    return ws_dir


def test_create_workspace(workspaces_dir):
    """WorkspaceService creates a new workspace directory with metadata."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspace = service.create_workspace("My Workspace", user_id="u-test")

    assert workspace.name == "My Workspace"
    assert workspace.user_id == "u-test"
    assert (workspaces_dir / workspace.id).exists()
    assert (workspaces_dir / workspace.id / "metadata.json").exists()


def test_list_workspaces_empty(workspaces_dir):
    """WorkspaceService returns empty list when no workspaces exist."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspaces = service.list_workspaces()

    assert workspaces == []


def test_list_workspaces_returns_all(workspaces_dir):
    """WorkspaceService lists all created workspaces."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    service.create_workspace("Workspace 1", user_id="u-test")
    service.create_workspace("Workspace 2", user_id="u-test")

    workspaces = service.list_workspaces()

    assert len(workspaces) == 2


def test_delete_workspace(workspaces_dir):
    """WorkspaceService deletes a workspace and its contents."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspace = service.create_workspace("To Delete", user_id="u-test")
    ws_path = workspaces_dir / workspace.id

    assert ws_path.exists()

    service.delete_workspace(workspace.id)

    assert not ws_path.exists()


def test_get_workspace(workspaces_dir):
    """WorkspaceService retrieves a workspace by ID."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    created = service.create_workspace("Test WS", user_id="u-test")

    retrieved = service.get_workspace(created.id)

    assert retrieved.id == created.id
    assert retrieved.name == "Test WS"
    assert retrieved.user_id == "u-test"


def test_get_workspace_not_found(workspaces_dir):
    """WorkspaceService raises exception for non-existent workspace."""
    from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

    service = WorkspaceService(workspaces_dir)

    with pytest.raises(WorkspaceNotFoundError):
        service.get_workspace("nonexistent-id")


def test_list_workspaces_for_user(workspaces_dir):
    """WorkspaceService lists only workspaces belonging to a specific user."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    service.create_workspace("User1 WS1", user_id="u-user1")
    service.create_workspace("User1 WS2", user_id="u-user1")
    service.create_workspace("User2 WS1", user_id="u-user2")

    user1_workspaces = service.list_workspaces_for_user("u-user1")
    user2_workspaces = service.list_workspaces_for_user("u-user2")

    assert len(user1_workspaces) == 2
    assert all(ws.user_id == "u-user1" for ws in user1_workspaces)
    assert len(user2_workspaces) == 1
    assert user2_workspaces[0].user_id == "u-user2"


def test_list_workspaces_for_user_empty(workspaces_dir):
    """WorkspaceService returns empty list when user has no workspaces."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    service.create_workspace("Other WS", user_id="u-other")

    workspaces = service.list_workspaces_for_user("u-noworkspaces")

    assert workspaces == []


def test_init_organization_workspace_creates_workspace(workspaces_dir):
    """init_organization_workspace creates org workspace if missing."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)

    service.init_organization_workspace()

    org_dir = workspaces_dir / "organization"
    assert org_dir.exists()
    assert (org_dir / "metadata.json").exists()
    assert (org_dir / "category_definitions.json").exists()
    assert (org_dir / "few_shot_examples.json").exists()
    assert (org_dir / "system_prompt.json").exists()
    assert (org_dir / "change_requests").is_dir()

    # Verify metadata has correct values
    metadata = service.get_workspace("organization")
    assert metadata.id == "organization"
    assert metadata.name == "Organization"
    assert metadata.user_id is None
    assert metadata.is_organization is True


def test_init_organization_workspace_skips_if_exists(workspaces_dir):
    """init_organization_workspace does nothing if workspace exists."""
    import json

    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)

    # Create org workspace with custom name first
    service.init_organization_workspace()
    org_dir = workspaces_dir / "organization"
    with open(org_dir / "metadata.json", "r") as f:
        metadata = json.load(f)
    metadata["name"] = "Custom Org Name"
    with open(org_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    # Call init again
    service.init_organization_workspace()

    # Verify name wasn't overwritten
    retrieved = service.get_workspace("organization")
    assert retrieved.name == "Custom Org Name"


def test_list_workspaces_includes_organization(workspaces_dir):
    """list_workspaces_for_user includes organization workspace first."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)

    # Init org workspace and create user workspace
    service.init_organization_workspace()
    service.create_workspace("User Workspace", user_id="u-user1")

    workspaces = service.list_workspaces_for_user("u-user1")

    # Org workspace should be first
    assert len(workspaces) == 2
    assert workspaces[0].id == "organization"
    assert workspaces[0].is_organization is True
    assert workspaces[1].is_organization is False


def test_cannot_delete_organization_workspace(workspaces_dir):
    """delete_workspace raises error for organization workspace."""
    from app.services.workspace_service import (
        OrganizationWorkspaceProtectedError,
        WorkspaceService,
    )

    service = WorkspaceService(workspaces_dir)
    service.init_organization_workspace()

    with pytest.raises(OrganizationWorkspaceProtectedError):
        service.delete_workspace("organization")
