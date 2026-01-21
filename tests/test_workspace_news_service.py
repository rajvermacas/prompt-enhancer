import pytest
from pathlib import Path


@pytest.fixture
def workspaces_dir(tmp_path):
    """Create a temporary workspaces directory with a workspace."""
    ws_dir = tmp_path / "workspaces"
    ws_dir.mkdir()
    return ws_dir


@pytest.fixture
def workspace_with_metadata(workspaces_dir):
    """Create a workspace directory with metadata."""
    import json
    from datetime import datetime

    ws_id = "ws-test123"
    ws_path = workspaces_dir / ws_id
    ws_path.mkdir()
    (ws_path / "feedback").mkdir()
    (ws_path / "evaluation_reports").mkdir()

    metadata = {
        "id": ws_id,
        "name": "Test Workspace",
        "created_at": datetime.now().isoformat(),
        "news_source": "merge"
    }
    with open(ws_path / "metadata.json", "w") as f:
        json.dump(metadata, f)

    return ws_id


def test_get_uploaded_news_path(workspaces_dir, workspace_with_metadata):
    """WorkspaceNewsService returns correct path for uploaded news CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    path = service._get_uploaded_news_path(workspace_with_metadata)

    assert path == workspaces_dir / workspace_with_metadata / "uploaded_news.csv"
