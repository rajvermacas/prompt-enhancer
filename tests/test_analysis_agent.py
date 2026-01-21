from unittest.mock import MagicMock


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


def test_analysis_agent_coerces_invalid_category_using_excerpt():
    """AnalysisAgent coerces invalid category based on category_excerpt matching."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.feedback import AIInsight, ReasoningRow
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    # Mock with_structured_output to return an AIInsight with invalid category
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_structured_llm.invoke.return_value = AIInsight(
        category="Neutral News",  # Invalid category, not in allowed set
        reasoning_table=[
            ReasoningRow(category_excerpt="Definition B", news_excerpt="x", reasoning="y")
        ],
        confidence=0.9,
    )

    agent = AnalysisAgent(llm=mock_llm, system_prompt="sys")
    categories = [
        CategoryDefinition(name="A", definition="Definition A"),
        CategoryDefinition(name="B", definition="Definition B"),
    ]

    insight = agent.analyze(categories, [], "article")

    assert insight.category == "B"


def test_analysis_agent_build_prompt_includes_additional_instructions():
    """AnalysisAgent includes Additional Instructions section when custom_system_prompt provided."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [CategoryDefinition(name="Cat1", definition="Definition 1")]

    prompt = agent._build_prompt(
        categories,
        [],
        "Test article",
        custom_system_prompt="Explain why other categories were not selected",
    )

    assert "## Additional Instructions" in prompt
    assert "Explain why other categories were not selected" in prompt
    assert "user_requested_analysis" in prompt


def test_analysis_agent_build_prompt_no_additional_instructions_when_none():
    """AnalysisAgent omits Additional Instructions section when custom_system_prompt is None."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [CategoryDefinition(name="Cat1", definition="Definition 1")]

    prompt = agent._build_prompt(categories, [], "Test article", custom_system_prompt=None)

    assert "## Additional Instructions" not in prompt
    assert "user_requested_analysis" not in prompt


def test_analysis_agent_analyze_with_custom_prompt_returns_ai_insight_with_user_analysis():
    """AnalysisAgent.analyze() returns AIInsightWithUserAnalysis when custom_system_prompt provided."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.feedback import AIInsightWithUserAnalysis
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_structured_llm.invoke.return_value = AIInsightWithUserAnalysis(
        category="Cat1",
        reasoning_table=[],
        confidence=0.9,
        user_requested_analysis="Custom analysis result",
    )

    agent = AnalysisAgent(llm=mock_llm, system_prompt="sys")
    categories = [CategoryDefinition(name="Cat1", definition="Definition 1")]

    insight = agent.analyze(categories, [], "article", custom_system_prompt="Explain rejection")

    mock_llm.with_structured_output.assert_called_once_with(AIInsightWithUserAnalysis)
    assert isinstance(insight, AIInsightWithUserAnalysis)
    assert insight.user_requested_analysis == "Custom analysis result"
