from datetime import datetime


def test_workspace_metadata_creation():
    """WorkspaceMetadata can be created with required fields."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-001",
        name="Test Workspace",
        created_at=datetime.now(),
    )

    assert metadata.id == "ws-001"
    assert metadata.name == "Test Workspace"
    assert metadata.description is None


def test_workspace_metadata_with_description():
    """WorkspaceMetadata can include optional description."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-002",
        name="Detailed Workspace",
        created_at=datetime.now(),
        description="A workspace for testing",
    )

    assert metadata.description == "A workspace for testing"
