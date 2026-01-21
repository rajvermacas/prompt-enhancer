from unittest.mock import MagicMock


def test_chat_reasoning_agent_builds_system_message():
    """ChatReasoningAgent includes all context in system message."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.feedback import AIInsight, ReasoningRow
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = ChatReasoningAgent(llm=mock_llm)

    insight = AIInsight(
        category="Tech",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="technology news",
                news_excerpt="Apple released iPhone",
                reasoning="matches tech definition"
            )
        ],
        confidence=0.85
    )

    categories = [
        CategoryDefinition(name="Tech", definition="Technology news"),
        CategoryDefinition(name="Business", definition="Business news"),
    ]

    few_shots = [
        FewShotExample(
            id="ex1",
            news_content="Google announced",
            category="Tech",
            reasoning="Tech company news"
        )
    ]

    article_content = "Apple released the new iPhone today."

    system_msg = agent._build_system_message(
        article_content=article_content,
        categories=categories,
        few_shots=few_shots,
        ai_insight=insight
    )

    assert "Apple released the new iPhone" in system_msg
    assert "Technology news" in system_msg
    assert "Business news" in system_msg
    assert "Google announced" in system_msg
    assert "Tech" in system_msg
    assert "0.85" in system_msg or "85" in system_msg


def test_chat_reasoning_agent_builds_messages_with_history():
    """ChatReasoningAgent includes chat history in messages."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.chat import ChatMessage

    mock_llm = MagicMock()
    agent = ChatReasoningAgent(llm=mock_llm)

    chat_history = [
        ChatMessage(role="user", content="Why Tech?"),
        ChatMessage(role="assistant", content="Because it matches."),
    ]

    messages = agent._build_messages(
        system_message="You are helpful.",
        chat_history=chat_history,
        current_message="What about Business?"
    )

    assert len(messages) == 4
    assert messages[0].content == "You are helpful."
    assert messages[1].content == "Why Tech?"
    assert messages[2].content == "Because it matches."
    assert messages[3].content == "What about Business?"


def test_chat_reasoning_agent_stream_yields_tokens():
    """ChatReasoningAgent.stream yields tokens from LLM."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.feedback import AIInsight
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    mock_chunks = [
        MagicMock(content="I "),
        MagicMock(content="classified "),
        MagicMock(content="this."),
    ]
    mock_llm.stream.return_value = iter(mock_chunks)

    agent = ChatReasoningAgent(llm=mock_llm)

    insight = AIInsight(category="Tech", reasoning_table=[], confidence=0.9)
    categories = [CategoryDefinition(name="Tech", definition="Tech news")]

    tokens = list(agent.stream(
        article_content="Test article",
        categories=categories,
        few_shots=[],
        ai_insight=insight,
        chat_history=[],
        message="Why?"
    ))

    assert tokens == ["I ", "classified ", "this."]
    mock_llm.stream.assert_called_once()
