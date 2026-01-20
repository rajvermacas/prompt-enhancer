from unittest.mock import MagicMock

import pytest


def test_improvement_agent_builds_prompt():
    """ImprovementAgent builds prompt from all reports."""
    from app.agents.improvement_agent import ImprovementAgent
    from app.models.feedback import EvaluationReport, PromptGap
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    reports = [
        EvaluationReport(
            id="rpt-001",
            feedback_id="fb-001",
            diagnosis="Issue 1",
            prompt_gaps=[PromptGap(location="Cat1", issue="Vague", suggestion="Fix")],
            few_shot_gaps=[],
            summary="Summary 1",
        ),
    ]
    categories = [CategoryDefinition(name="Cat1", definition="Def1")]

    prompt = agent._build_prompt(reports, categories, [])

    assert "Issue 1" in prompt
    assert "Cat1" in prompt


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
