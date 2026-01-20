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
    workspace = service.create_workspace("My Workspace")

    assert workspace.name == "My Workspace"
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
    service.create_workspace("Workspace 1")
    service.create_workspace("Workspace 2")

    workspaces = service.list_workspaces()

    assert len(workspaces) == 2


def test_delete_workspace(workspaces_dir):
    """WorkspaceService deletes a workspace and its contents."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspace = service.create_workspace("To Delete")
    ws_path = workspaces_dir / workspace.id

    assert ws_path.exists()

    service.delete_workspace(workspace.id)

    assert not ws_path.exists()


def test_get_workspace(workspaces_dir):
    """WorkspaceService retrieves a workspace by ID."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    created = service.create_workspace("Test WS")

    retrieved = service.get_workspace(created.id)

    assert retrieved.id == created.id
    assert retrieved.name == "Test WS"


def test_get_workspace_not_found(workspaces_dir):
    """WorkspaceService raises exception for non-existent workspace."""
    from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

    service = WorkspaceService(workspaces_dir)

    with pytest.raises(WorkspaceNotFoundError):
        service.get_workspace("nonexistent-id")
