from unittest.mock import MagicMock

import pytest


def test_analysis_agent_builds_prompt():
    """AnalysisAgent builds prompt from all three dimensions."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [
        CategoryDefinition(name="Cat1", definition="Definition 1"),
    ]
    few_shots = [
        FewShotExample(id="ex1", news_content="News 1", category="Cat1", reasoning="R1"),
    ]

    prompt = agent._build_prompt(categories, few_shots, "Test article content")

    assert "Allowed category names" in prompt
    assert "Cat1" in prompt
    assert "Definition 1" in prompt
    assert "News 1" in prompt
    assert "Test article content" in prompt
    assert "You are an analyst." not in prompt


def test_analysis_agent_parses_response():
    """AnalysisAgent parses LLM response into AIInsight."""
    from app.agents.analysis_agent import AnalysisAgent

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="Test")

    raw_response = '''{
        "category": "Cat1",
        "reasoning_table": [
            {"category_excerpt": "exc1", "news_excerpt": "exc2", "reasoning": "r1"}
        ],
        "confidence": 0.85
    }'''

    insight = agent._parse_response(raw_response)

    assert insight.category == "Cat1"
    assert insight.confidence == 0.85
    assert len(insight.reasoning_table) == 1


def test_analysis_agent_coerces_invalid_category_using_excerpt():
    """AnalysisAgent coerces invalid category based on category_excerpt matching."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    raw_response = '''{
        "category": "Neutral News",
        "reasoning_table": [
            {"category_excerpt": "Definition B", "news_excerpt": "x", "reasoning": "y"}
        ],
        "confidence": 0.9
    }'''
    mock_llm.invoke.return_value = MagicMock(content=raw_response)

    agent = AnalysisAgent(llm=mock_llm, system_prompt="sys")
    categories = [
        CategoryDefinition(name="A", definition="Definition A"),
        CategoryDefinition(name="B", definition="Definition B"),
    ]

    insight = agent.analyze(categories, [], "article")

    assert insight.category == "B"
