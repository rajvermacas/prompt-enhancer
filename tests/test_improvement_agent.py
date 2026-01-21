from unittest.mock import MagicMock

import pytest


def test_improvement_agent_builds_prompt_from_feedbacks():
    """ImprovementAgent builds prompt from feedbacks with full context."""
    from datetime import datetime
    from unittest.mock import MagicMock

    from app.agents.improvement_agent import ImprovementAgent
    from app.models.feedback import AIInsight, FeedbackWithHeadline, ReasoningRow
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    feedbacks = [
        FeedbackWithHeadline(
            id="fb-001",
            article_id="news-001",
            article_headline="Company X Reports Earnings",
            article_content="Full article about Company X earnings report...",
            thumbs_up=False,
            correct_category="Financial News",
            reasoning="This is about earnings, not technology",
            ai_insight=AIInsight(
                category="Technology",
                reasoning_table=[
                    ReasoningRow(
                        category_excerpt="tech companies",
                        news_excerpt="Company X",
                        reasoning="Company X is tech",
                    )
                ],
                confidence=0.75,
            ),
            created_at=datetime.now(),
        ),
    ]
    categories = [CategoryDefinition(name="Technology", definition="Tech news")]

    prompt = agent._build_prompt(feedbacks, categories, [])

    assert "fb-001" in prompt
    assert "Company X Reports Earnings" in prompt
    assert "Full article about Company X earnings report" in prompt
    assert "This is about earnings, not technology" in prompt
    assert "Financial News" in prompt
    assert "AUTHORITATIVE" in prompt


def test_improvement_agent_parses_response():
    """ImprovementAgent parses response into suggestions."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [{"category": "Cat1", "current": "Def1", "suggested": "Better def", "rationale": "Clearer"}],
        "few_shot_suggestions": [],
        "priority_order": ["Fix Cat1 first"]
    }'''

    result = agent._parse_response(raw_response)

    assert len(result.category_suggestions) == 1
    assert result.priority_order[0] == "Fix Cat1 first"


def test_improvement_agent_parses_updated_fields():
    """ImprovementAgent parses updated categories and few-shots."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [],
        "few_shot_suggestions": [],
        "priority_order": [],
        "updated_categories": [{"category": "Cat1", "updated_definition": "New def"}],
        "updated_few_shots": [{"action": "add", "example": {"id": "ex-1", "news_content": "News", "category": "Cat1", "reasoning": "Reason"}}]
    }'''

    result = agent._parse_response(raw_response)

    assert result.updated_categories[0].category == "Cat1"
    assert result.updated_few_shots[0].action == "add"


def test_improvement_agent_parses_complete_few_shot_with_source():
    """ImprovementAgent parses complete few-shot suggestions with source field."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [],
        "few_shot_suggestions": [
            {
                "action": "add",
                "source": "user_article",
                "based_on_feedback_id": "fb-001",
                "details": {
                    "id": "example_positive_1",
                    "news_content": "Company X reports record earnings.",
                    "category": "Positive News",
                    "reasoning": "Strong earnings indicate positive sentiment."
                }
            }
        ],
        "priority_order": [],
        "updated_few_shots": [
            {
                "action": "add",
                "source": "user_article",
                "example": {
                    "id": "example_positive_1",
                    "news_content": "Company X reports record earnings.",
                    "category": "Positive News",
                    "reasoning": "Strong earnings indicate positive sentiment."
                }
            }
        ]
    }'''

    result = agent._parse_response(raw_response)

    assert result.updated_few_shots[0].example.news_content == "Company X reports record earnings."
    assert result.updated_few_shots[0].example.category == "Positive News"
    assert result.updated_few_shots[0].example.reasoning == "Strong earnings indicate positive sentiment."
    assert result.few_shot_suggestions[0]["source"] == "user_article"
    assert result.few_shot_suggestions[0]["based_on_feedback_id"] == "fb-001"
