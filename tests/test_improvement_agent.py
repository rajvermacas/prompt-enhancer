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
