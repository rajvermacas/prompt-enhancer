import io

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


def test_add_article_creates_csv(workspaces_dir, workspace_with_metadata):
    """add_article creates uploaded_news.csv if it doesn't exist."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    article = service.add_article(
        workspace_with_metadata,
        headline="Test Headline",
        content="Test content",
        date="2026-01-15"
    )

    assert article.headline == "Test Headline"
    assert article.content == "Test content"
    assert article.date == "2026-01-15"
    assert article.id is not None
    assert (workspaces_dir / workspace_with_metadata / "uploaded_news.csv").exists()


def test_add_article_appends_to_existing_csv(workspaces_dir, workspace_with_metadata):
    """add_article appends to existing CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    service.add_article(workspace_with_metadata, "First", "Content 1", "2026-01-01")
    service.add_article(workspace_with_metadata, "Second", "Content 2", "2026-01-02")

    csv_path = workspaces_dir / workspace_with_metadata / "uploaded_news.csv"
    with open(csv_path) as f:
        lines = f.readlines()

    assert len(lines) == 3  # header + 2 articles


def test_upload_csv_success(workspaces_dir, workspace_with_metadata):
    """upload_csv parses and stores articles from CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    csv_content = "id,headline,content,date\n1,News One,Content one,2026-01-01\n2,News Two,Content two,2026-01-02"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    count = service.upload_csv(workspace_with_metadata, file)

    assert count == 2
    assert (workspaces_dir / workspace_with_metadata / "uploaded_news.csv").exists()


def test_upload_csv_missing_columns(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error when required columns are missing."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline\n1,News One"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "content" in str(exc.value).lower()
    assert "date" in str(exc.value).lower()


def test_upload_csv_empty_file(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error for empty CSV."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline,content,date\n"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "empty" in str(exc.value).lower()


def test_upload_csv_duplicate_ids(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error for duplicate IDs in file."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline,content,date\n1,News One,Content,2026-01-01\n1,Duplicate,Content,2026-01-02"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "duplicate" in str(exc.value).lower()


def test_get_news_source_default(workspaces_dir, workspace_with_metadata):
    """get_news_source returns merge by default."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    source = service.get_news_source(workspace_with_metadata)

    assert source == NewsSource.MERGE


def test_set_news_source(workspaces_dir, workspace_with_metadata):
    """set_news_source updates workspace metadata."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    service.set_news_source(workspace_with_metadata, NewsSource.REPLACE)
    source = service.get_news_source(workspace_with_metadata)

    assert source == NewsSource.REPLACE
