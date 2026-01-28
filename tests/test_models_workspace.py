import pytest
from datetime import datetime


def test_workspace_metadata_creation():
    """WorkspaceMetadata can be created with required fields."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-001",
        name="Test Workspace",
        created_at=datetime.now(),
        user_id="u-test",
    )

    assert metadata.id == "ws-001"
    assert metadata.name == "Test Workspace"
    assert metadata.description is None
    assert metadata.user_id == "u-test"


def test_workspace_metadata_with_description():
    """WorkspaceMetadata can include optional description."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-002",
        name="Detailed Workspace",
        created_at=datetime.now(),
        description="A workspace for testing",
        user_id="u-test",
    )

    assert metadata.description == "A workspace for testing"


def test_workspace_metadata_news_source_default():
    """WorkspaceMetadata news_source defaults to merge."""
    from app.models.workspace import WorkspaceMetadata
    from app.models.news import NewsSource

    metadata = WorkspaceMetadata(
        id="ws-123",
        name="Test",
        created_at=datetime.now(),
        user_id="u-test",
    )

    assert metadata.news_source == NewsSource.MERGE


def test_workspace_metadata_news_source_replace():
    """WorkspaceMetadata accepts replace news_source."""
    from app.models.workspace import WorkspaceMetadata
    from app.models.news import NewsSource

    metadata = WorkspaceMetadata(
        id="ws-123",
        name="Test",
        created_at=datetime.now(),
        news_source=NewsSource.REPLACE,
        user_id="u-test",
    )

    assert metadata.news_source == NewsSource.REPLACE


def test_workspace_metadata_requires_user_id():
    """WorkspaceMetadata requires user_id field."""
    from pydantic import ValidationError
    from app.models.workspace import WorkspaceMetadata

    ws = WorkspaceMetadata(
        id="ws-123",
        name="Test",
        created_at=datetime.now(),
        user_id="u-abc",
    )
    assert ws.user_id == "u-abc"

    with pytest.raises(ValidationError):
        WorkspaceMetadata(
            id="ws-123",
            name="Test",
            created_at=datetime.now(),
        )
