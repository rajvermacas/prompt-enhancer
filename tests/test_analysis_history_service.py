from datetime import datetime, timedelta

import pytest


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_auth.db")


@pytest.fixture
def service(db_path):
    from app.db import init_db
    from app.services.analysis_history_service import AnalysisHistoryService

    init_db(db_path)
    return AnalysisHistoryService(db_path)


def _insight_payload(category: str, user_text: str) -> dict:
    return {
        "category": category,
        "confidence": 0.92,
        "reasoning_table": [
            {
                "category_excerpt": "Category snippet",
                "news_excerpt": "News snippet",
                "reasoning": "Why this category",
            }
        ],
        "user_requested_analysis": user_text,
    }


def test_save_and_list_runs_newest_first(service):
    run_one = service.save_run(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        insight_payload=_insight_payload("Tech", "first"),
        created_at=datetime(2026, 2, 8, 10, 0, 0),
    )
    run_two = service.save_run(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        insight_payload=_insight_payload("Finance", "second"),
        created_at=datetime(2026, 2, 8, 10, 5, 0),
    )

    page = service.list_runs(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        page=1,
        limit=10,
    )

    assert page.total == 2
    assert page.has_next is False
    assert [item.id for item in page.items] == [run_two.id, run_one.id]


def test_list_runs_is_scoped_to_triggering_user(service):
    service.save_run(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        insight_payload=_insight_payload("Tech", "mine"),
        created_at=datetime(2026, 2, 8, 10, 0, 0),
    )
    service.save_run(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-2",
        insight_payload=_insight_payload("Sports", "other"),
        created_at=datetime(2026, 2, 8, 10, 1, 0),
    )

    page = service.list_runs(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        page=1,
        limit=10,
    )

    assert page.total == 1
    assert len(page.items) == 1
    assert page.items[0].triggered_user_id == "u-1"


def test_list_runs_supports_pagination(service):
    start = datetime(2026, 2, 8, 10, 0, 0)
    for offset in range(11):
        service.save_run(
            workspace_id="ws-1",
            article_id="news-1",
            triggered_user_id="u-1",
            insight_payload=_insight_payload("Tech", f"run-{offset}"),
            created_at=start + timedelta(minutes=offset),
        )

    first_page = service.list_runs(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        page=1,
        limit=10,
    )
    second_page = service.list_runs(
        workspace_id="ws-1",
        article_id="news-1",
        triggered_user_id="u-1",
        page=2,
        limit=10,
    )

    assert first_page.total == 11
    assert len(first_page.items) == 10
    assert first_page.has_next is True
    assert len(second_page.items) == 1
    assert second_page.has_next is False
