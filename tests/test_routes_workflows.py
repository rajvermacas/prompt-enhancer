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

    from app.main import app

    return TestClient(app)


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


def test_analyze_article(client, workspace_id):
    """POST /api/workspaces/{id}/analyze runs analysis agent."""
    mock_insight = {
        "category": "Cat1",
        "reasoning_table": [],
        "confidence": 0.9,
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = str(mock_insight).replace("'", '"')
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
                "note": "Good",
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
