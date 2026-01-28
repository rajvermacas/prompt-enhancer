import csv
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with workspace and news."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))

    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        writer.writerow({"id": "news-001", "headline": "Test", "content": "Content"})

    monkeypatch.setenv("NEWS_CSV_PATH", str(csv_path))
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
    """Create workspace with categories."""
    response = client.post("/api/workspaces", json={"name": "Test"})
    ws_id = response.json()["id"]

    # Add categories
    client.put(
        f"/api/workspaces/{ws_id}/prompts/categories",
        json={"categories": [{"name": "Cat1", "definition": "Def1"}]},
    )
    return ws_id


def test_analyze_article_no_categories_returns_400(client):
    """POST /api/workspaces/{id}/analyze returns 400 when no categories defined."""
    # Create workspace without categories
    response = client.post("/api/workspaces", json={"name": "Empty"})
    ws_id = response.json()["id"]

    response = client.post(
        f"/api/workspaces/{ws_id}/analyze",
        json={"article_id": "news-001"},
    )

    assert response.status_code == 400
    assert "No categories defined" in response.json()["detail"]


def test_analyze_article(client, workspace_id):
    """POST /api/workspaces/{id}/analyze runs analysis agent."""
    from app.models.feedback import AIInsight

    mock_insight = AIInsight(
        category="Cat1",
        reasoning_table=[],
        confidence=0.9,
    )

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = mock_insight
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/analyze",
            json={"article_id": "news-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "category" in data


def test_submit_feedback(client, workspace_id):
    """POST /api/workspaces/{id}/feedback saves feedback and runs evaluation."""
    mock_report = {
        "diagnosis": "Test",
        "prompt_gaps": [],
        "few_shot_gaps": [],
        "summary": "Test summary",
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = str(mock_report).replace("'", '"')
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/feedback",
            json={
                "article_id": "news-001",
                "thumbs_up": True,
                "correct_category": "Cat1",
                "reasoning": "Correct",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.9,
                },
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data


def test_chat_reasoning_streams_response(client, workspace_id):
    """POST /api/workspaces/{id}/chat-reasoning streams SSE tokens."""
    mock_chunks = [
        MagicMock(content="I "),
        MagicMock(content="chose "),
        MagicMock(content="Tech."),
    ]

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.stream.return_value = iter(mock_chunks)
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/chat-reasoning",
            json={
                "article_id": "news-001",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.9,
                },
                "message": "Why this category?",
                "chat_history": [],
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.text
    assert 'data: {"token": "I "}' in content
    assert 'data: {"token": "chose "}' in content
    assert 'data: {"token": "Tech."}' in content
    assert 'data: {"done": true}' in content


def test_chat_reasoning_workspace_not_found(client):
    """POST /api/workspaces/{id}/chat-reasoning returns 404 for missing workspace."""
    response = client.post(
        "/api/workspaces/nonexistent/chat-reasoning",
        json={
            "article_id": "news-001",
            "ai_insight": {
                "category": "Cat1",
                "reasoning_table": [],
                "confidence": 0.9,
            },
            "message": "Why?",
            "chat_history": [],
        },
    )
    assert response.status_code == 404


def test_chat_reasoning_article_not_found(client, workspace_id):
    """POST /api/workspaces/{id}/chat-reasoning returns 404 for missing article."""
    response = client.post(
        f"/api/workspaces/{workspace_id}/chat-reasoning",
        json={
            "article_id": "nonexistent",
            "ai_insight": {
                "category": "Cat1",
                "reasoning_table": [],
                "confidence": 0.9,
            },
            "message": "Why?",
            "chat_history": [],
        },
    )
    assert response.status_code == 404


def test_feedback_with_headlines_includes_content(client, workspace_id):
    """GET /api/workspaces/{id}/feedback-with-headlines returns article_content."""
    # First submit feedback
    mock_report = {
        "diagnosis": "Test",
        "prompt_gaps": [],
        "few_shot_gaps": [],
        "summary": "Test summary",
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = str(mock_report).replace("'", '"')
        mock_get_llm.return_value = mock_llm

        client.post(
            f"/api/workspaces/{workspace_id}/feedback",
            json={
                "article_id": "news-001",
                "thumbs_up": False,
                "correct_category": "Cat2",
                "reasoning": "Wrong category",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.8,
                },
            },
        )

    response = client.get(f"/api/workspaces/{workspace_id}/feedback-with-headlines")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["article_content"] == "Content"


def test_analyze_article_with_system_prompt(client, workspace_id):
    """POST /api/workspaces/{id}/analyze includes user_requested_analysis when system prompt set."""
    from app.models.feedback import AIInsightWithUserAnalysis

    # First set a system prompt
    client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json={"content": "Explain why other categories were not selected"},
    )

    mock_insight = AIInsightWithUserAnalysis(
        category="Cat1",
        reasoning_table=[],
        confidence=0.9,
        user_requested_analysis="Other categories were not selected because...",
    )

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        # Mock with_structured_output to return a mock that returns our insight
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_insight
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/analyze",
            json={"article_id": "news-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "user_requested_analysis" in data
