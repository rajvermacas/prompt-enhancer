from datetime import datetime
from unittest.mock import MagicMock

import pytest


def test_evaluation_agent_builds_prompt():
    """EvaluationAgent builds prompt with feedback context."""
    from app.agents.evaluation_agent import EvaluationAgent
    from app.models.feedback import AIInsight, Feedback
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = EvaluationAgent(llm=mock_llm)

    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=False,
        correct_category="Cat2",
        reasoning="Wrong category",
        note="Should be Cat2",
        ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.8),
        created_at=datetime.now(),
    )
    categories = [CategoryDefinition(name="Cat1", definition="Def1")]
    few_shots = []

    prompt = agent._build_prompt(feedback, categories, few_shots)

    assert "Cat1" in prompt
    assert "Cat2" in prompt
    assert "Thumbs up: False" in prompt or "negative" in prompt.lower()


def test_evaluation_agent_parses_response():
    """EvaluationAgent parses LLM response into EvaluationReport."""
    from app.agents.evaluation_agent import EvaluationAgent

    mock_llm = MagicMock()
    agent = EvaluationAgent(llm=mock_llm)

    raw_response = '''{
        "diagnosis": "Category definition unclear",
        "prompt_gaps": [{"location": "Cat1", "issue": "Vague", "suggestion": "Clarify"}],
        "few_shot_gaps": [],
        "summary": "Improve Cat1 definition"
    }'''

    report = agent._parse_response("fb-001", raw_response)

    assert report.feedback_id == "fb-001"
    assert report.diagnosis == "Category definition unclear"
    assert len(report.prompt_gaps) == 1
