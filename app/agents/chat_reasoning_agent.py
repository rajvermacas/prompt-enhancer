from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.models.chat import ChatMessage
from app.models.feedback import AIInsight
from app.models.prompts import CategoryDefinition, FewShotExample


class ChatReasoningAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def stream(
        self,
        article_content: str,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        ai_insight: AIInsight,
        chat_history: list[ChatMessage],
        message: str,
    ) -> Iterator[str]:
        system_message = self._build_system_message(
            article_content=article_content,
            categories=categories,
            few_shots=few_shots,
            ai_insight=ai_insight,
        )

        messages = self._build_messages(
            system_message=system_message,
            chat_history=chat_history,
            current_message=message,
        )

        for chunk in self.llm.stream(messages):
            if chunk.content and isinstance(chunk.content, str):
                yield chunk.content

    def _build_system_message(
        self,
        article_content: str,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        ai_insight: AIInsight,
    ) -> str:
        parts = [
            "You are an AI assistant explaining your classification reasoning.",
            "You previously analyzed a news article and classified it into a category.",
            "Now the user wants to understand your thought process.",
            "",
            "YOUR ROLE:",
            "- Explain WHY you made the classification decision",
            "- Compare against other categories when asked",
            "- Reference specific excerpts from the article",
            "- Explain how few-shot examples influenced your thinking",
            "- Be honest about uncertainty or close calls",
            "",
            "DO NOT:",
            "- Re-classify the article",
            "- Change your original decision",
            "- Make up information not in the provided context",
            "",
            "## Original Article",
            article_content,
            "",
            "## Category Definitions Available",
        ]

        for cat in categories:
            parts.append(f"### {cat.name}")
            parts.append(f"{cat.definition}")
            parts.append("")

        if few_shots:
            parts.append("## Few-Shot Examples Used")
            for ex in few_shots:
                parts.append(f"- News: {ex.news_content}")
                parts.append(f"  Category: {ex.category}")
                parts.append(f"  Reasoning: {ex.reasoning}")
                parts.append("")

        parts.append("## Your Classification Result")
        parts.append(f"Category: {ai_insight.category}")
        parts.append(f"Confidence: {ai_insight.confidence:.0%}")
        parts.append("")
        parts.append("Reasoning Table:")
        for row in ai_insight.reasoning_table:
            parts.append(f"- Category Excerpt: {row.category_excerpt}")
            parts.append(f"  News Excerpt: {row.news_excerpt}")
            parts.append(f"  Reasoning: {row.reasoning}")

        return "\n".join(parts)

    def _build_messages(
        self,
        system_message: str,
        chat_history: list[ChatMessage],
        current_message: str,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=system_message)]

        for msg in chat_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=current_message))
        return messages
