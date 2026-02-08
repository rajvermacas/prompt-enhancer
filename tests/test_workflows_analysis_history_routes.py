from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.analysis_history import AnalysisHistoryPage, AnalysisRunEntry
from app.models.auth import User, UserRole
from app.models.feedback import AIInsight
from app.models.news import NewsArticle
from app.models.prompts import CategoryDefinition, PromptConfig
from app.models.workspace import WorkspaceMetadata
from app.routes import workflows
from app.services.prompt_service import PromptService


@pytest.fixture
def settings_and_workspace(tmp_path):
    workspaces_path = tmp_path / "workspaces"
    workspace_id = "ws-owner"
    workspace_dir = workspaces_path / workspace_id
    workspaces_path.mkdir()
    workspace_dir.mkdir()

    PromptService.initialize_prompt_storage(workspace_dir, updated_by="system")
    prompt_service = PromptService(workspace_dir)
    prompt_service.save_categories(
        config=PromptConfig(
            categories=[CategoryDefinition(name="Cat1", definition="Definition")]
        ),
        updated_by="u-owner",
        source="direct_save",
        change_request_id=None,
    )

    system_prompt_path = tmp_path / "system.txt"
    system_prompt_path.write_text("System prompt")

    settings = SimpleNamespace(
        workspaces_path=str(workspaces_path),
        system_prompt_path=str(system_prompt_path),
    )
    return settings, workspace_id


def _build_user(user_id: str) -> User:
    return User(
        id=user_id,
        email=f"{user_id}@example.com",
        created_at=datetime(2026, 2, 8, 12, 0, 0),
        role=UserRole.USER,
    )


def test_analyze_article_saves_history_entry(monkeypatch, settings_and_workspace):
    settings, workspace_id = settings_and_workspace
    current_user = _build_user("u-owner")

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id=workspace_id,
        name="Owner workspace",
        user_id=current_user.id,
        created_at=datetime(2026, 2, 8, 12, 0, 0),
    )

    workspace_news_service = MagicMock()
    workspace_news_service.get_article.return_value = NewsArticle(
        id="news-1",
        headline="Headline",
        content="Article body",
        date="2026-02-08",
    )

    history_service = MagicMock()
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = AIInsight(
        category="Cat1",
        reasoning_table=[],
        confidence=0.9,
    )
    mock_llm.with_structured_output.return_value = mock_structured_llm

    monkeypatch.setattr(workflows, "get_settings", lambda: settings)
    monkeypatch.setattr(workflows, "get_llm", lambda _: mock_llm)

    result = workflows.analyze_article(
        workspace_id=workspace_id,
        request=workflows.AnalyzeRequest(article_id="news-1"),
        current_user=current_user,
        workspace_service=workspace_service,
        workspace_news_service=workspace_news_service,
        analysis_history_service=history_service,
    )

    assert result.category == "Cat1"
    history_service.save_run.assert_called_once()
    saved_kwargs = history_service.save_run.call_args.kwargs
    assert saved_kwargs["workspace_id"] == workspace_id
    assert saved_kwargs["article_id"] == "news-1"
    assert saved_kwargs["triggered_user_id"] == current_user.id


def test_analyze_article_forbidden_for_non_owner(monkeypatch, settings_and_workspace):
    settings, workspace_id = settings_and_workspace
    monkeypatch.setattr(workflows, "get_settings", lambda: settings)

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id=workspace_id,
        name="Owner workspace",
        user_id="u-owner",
        created_at=datetime(2026, 2, 8, 12, 0, 0),
    )

    with pytest.raises(HTTPException) as exc:
        workflows.analyze_article(
            workspace_id=workspace_id,
            request=workflows.AnalyzeRequest(article_id="news-1"),
            current_user=_build_user("u-other"),
            workspace_service=workspace_service,
            workspace_news_service=MagicMock(),
            analysis_history_service=MagicMock(),
        )

    assert exc.value.status_code == 403


def test_get_analysis_history_returns_user_scoped_page(settings_and_workspace):
    _, workspace_id = settings_and_workspace
    current_user = _build_user("u-owner")

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id=workspace_id,
        name="Owner workspace",
        user_id=current_user.id,
        created_at=datetime(2026, 2, 8, 12, 0, 0),
    )

    expected_page = AnalysisHistoryPage(
        items=[
            AnalysisRunEntry(
                id="ar-1",
                workspace_id=workspace_id,
                article_id="news-1",
                triggered_user_id=current_user.id,
                insight={
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.9,
                    "user_requested_analysis": "Text",
                },
                created_at=datetime(2026, 2, 8, 12, 0, 0),
            )
        ],
        total=1,
        page=1,
        limit=10,
        has_next=False,
    )

    history_service = MagicMock()
    history_service.list_runs.return_value = expected_page

    result = workflows.get_analysis_history(
        workspace_id=workspace_id,
        article_id="news-1",
        page=1,
        limit=10,
        current_user=current_user,
        workspace_service=workspace_service,
        analysis_history_service=history_service,
    )

    assert result.total == 1
    history_service.list_runs.assert_called_once_with(
        workspace_id=workspace_id,
        article_id="news-1",
        triggered_user_id=current_user.id,
        page=1,
        limit=10,
    )


def test_get_analysis_history_rejects_invalid_limit(settings_and_workspace):
    _, workspace_id = settings_and_workspace
    current_user = _build_user("u-owner")

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id=workspace_id,
        name="Owner workspace",
        user_id=current_user.id,
        created_at=datetime(2026, 2, 8, 12, 0, 0),
    )

    with pytest.raises(HTTPException) as exc:
        workflows.get_analysis_history(
            workspace_id=workspace_id,
            article_id="news-1",
            page=1,
            limit=20,
            current_user=current_user,
            workspace_service=workspace_service,
            analysis_history_service=MagicMock(),
        )

    assert exc.value.status_code == 400


def test_get_analysis_history_forbidden_for_non_owner(settings_and_workspace):
    _, workspace_id = settings_and_workspace

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id=workspace_id,
        name="Owner workspace",
        user_id="u-owner",
        created_at=datetime(2026, 2, 8, 12, 0, 0),
    )

    with pytest.raises(HTTPException) as exc:
        workflows.get_analysis_history(
            workspace_id=workspace_id,
            article_id="news-1",
            page=1,
            limit=10,
            current_user=_build_user("u-other"),
            workspace_service=workspace_service,
            analysis_history_service=MagicMock(),
        )

    assert exc.value.status_code == 403


def test_get_analysis_history_allows_organization_workspace():
    current_user = _build_user("u-any")

    workspace_service = MagicMock()
    workspace_service.get_workspace.return_value = WorkspaceMetadata(
        id="organization",
        name="Organization",
        user_id=None,
        created_at=datetime(2026, 2, 8, 12, 0, 0),
        is_organization=True,
    )

    history_service = MagicMock()
    history_service.list_runs.return_value = AnalysisHistoryPage(
        items=[],
        total=0,
        page=1,
        limit=10,
        has_next=False,
    )

    result = workflows.get_analysis_history(
        workspace_id="organization",
        article_id="news-1",
        page=1,
        limit=10,
        current_user=current_user,
        workspace_service=workspace_service,
        analysis_history_service=history_service,
    )

    assert result.total == 0
