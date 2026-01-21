from typing import Literal

from pydantic import BaseModel

from app.models.feedback import AIInsight


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatReasoningRequest(BaseModel):
    article_id: str
    ai_insight: AIInsight
    message: str
    chat_history: list[ChatMessage]
