import pytest
from pydantic import ValidationError


def test_chat_message_valid():
    """ChatMessage accepts user and assistant roles."""
    from app.models.chat import ChatMessage

    user_msg = ChatMessage(role="user", content="Why this category?")
    assert user_msg.role == "user"
    assert user_msg.content == "Why this category?"

    assistant_msg = ChatMessage(role="assistant", content="Because...")
    assert assistant_msg.role == "assistant"


def test_chat_message_invalid_role():
    """ChatMessage rejects invalid roles."""
    from app.models.chat import ChatMessage

    with pytest.raises(ValidationError):
        ChatMessage(role="system", content="test")


def test_chat_reasoning_request_valid():
    """ChatReasoningRequest validates all fields."""
    from app.models.chat import ChatMessage, ChatReasoningRequest
    from app.models.feedback import AIInsight, ReasoningRow

    insight = AIInsight(
        category="Tech",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="tech news",
                news_excerpt="Apple released",
                reasoning="matches tech"
            )
        ],
        confidence=0.9
    )

    request = ChatReasoningRequest(
        article_id="news-001",
        ai_insight=insight,
        message="Why not Business?",
        chat_history=[ChatMessage(role="user", content="Hello")]
    )

    assert request.article_id == "news-001"
    assert request.message == "Why not Business?"
    assert len(request.chat_history) == 1
