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
