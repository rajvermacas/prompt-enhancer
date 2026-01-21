import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import (
    FeedbackWithHeadline,
    ImprovementSuggestion,
    UpdatedCategory,
)
from app.models.prompts import CategoryDefinition, FewShotExample


IMPROVEMENT_SYSTEM_PROMPT = """You are a prompt optimization expert. Analyze user feedback and suggest improvements to category definitions and few-shot examples.

CRITICAL: User feedback reasoning is AUTHORITATIVE. Your suggestions MUST directly address what the user explained. Do not override or reinterpret user reasoning with your own judgment.

For each suggestion, you MUST:
1. Reference which feedback ID(s) it addresses
2. Quote the specific user reasoning that drives this suggestion
3. Explain how your suggestion fixes the issue the user identified

When a user marks a classification as incorrect (thumbs down):
- Their correct_category IS the correct answer
- Their reasoning explains WHY - use this to improve definitions
- Consider proposing their article as a new few-shot example (source: "user_article")

You may also suggest synthetic few-shot examples (source: "synthetic") when you identify gaps that user articles don't cover.

Respond with a JSON object containing:
- category_suggestions: array of {category, current, suggested, rationale, based_on_feedback_ids, user_reasoning_quotes}
- few_shot_suggestions: array of {action: "add"|"modify"|"remove", source: "user_article"|"synthetic", based_on_feedback_id, details}
- priority_order: array of strings indicating what to fix first
- updated_few_shots: array of {action, source, example} for changed items only

Do NOT include updated_categories - it will be derived from category_suggestions.

Rules:
- Return ONLY valid JSON (no markdown).
- Every suggestion MUST have based_on_feedback_ids populated
- Every suggestion MUST quote relevant user reasoning
- For "user_article" few-shots, use the actual article content and user's correct category
"""


class ImprovementAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def suggest_improvements(
        self,
        feedbacks: list[FeedbackWithHeadline],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> ImprovementSuggestion:
        prompt = self._build_prompt(feedbacks, categories, few_shots)
        messages = [
            SystemMessage(content=IMPROVEMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        feedbacks: list[FeedbackWithHeadline],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## User Feedback (AUTHORITATIVE)\n\n"]

        for fb in feedbacks:
            parts.append(f"### Feedback {fb.id}\n")
            parts.append(f"**Article Headline:** {fb.article_headline}\n")
            parts.append(f"**Article Content:**\n{fb.article_content}\n\n")
            verdict = "Correct" if fb.thumbs_up else "Incorrect"
            parts.append(f"**User Verdict:** {verdict}\n")
            if not fb.thumbs_up:
                parts.append(f"**User's Correct Category:** {fb.correct_category}\n")
            parts.append(f"**User's Reasoning (AUTHORITATIVE):** {fb.reasoning}\n")
            confidence_pct = f"{fb.ai_insight.confidence:.0%}"
            parts.append(f"**AI Predicted:** {fb.ai_insight.category} ({confidence_pct} confidence)\n")
            if fb.ai_insight.reasoning_table:
                parts.append("**AI Reasoning Table:**\n")
                for row in fb.ai_insight.reasoning_table:
                    parts.append(f"  - {row.category_excerpt} | {row.news_excerpt} | {row.reasoning}\n")
            parts.append("\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"### {ex.id}\n")
                parts.append(f"- Category: {ex.category}\n")
                parts.append(f"- Content: {ex.news_content}\n")
                parts.append(f"- Reasoning: {ex.reasoning}\n\n")

        return "".join(parts)

    def _derive_updated_categories(
        self, category_suggestions: list[dict]
    ) -> list[UpdatedCategory]:
        """Derive updated_categories from category_suggestions for guaranteed traceability."""
        return [
            UpdatedCategory(
                category=s["category"],
                updated_definition=s["suggested"],
                based_on_feedback_ids=s.get("based_on_feedback_ids", []),
                rationale=s.get("rationale", ""),
            )
            for s in category_suggestions
            if s.get("category") and s.get("suggested")
        ]

    def _parse_response(self, response: str) -> ImprovementSuggestion:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())

        category_suggestions = data.get("category_suggestions", [])
        updated_categories = self._derive_updated_categories(category_suggestions)

        return ImprovementSuggestion(
            category_suggestions=category_suggestions,
            few_shot_suggestions=data.get("few_shot_suggestions", []),
            priority_order=data.get("priority_order", []),
            updated_categories=updated_categories,
            updated_few_shots=data.get("updated_few_shots", []),
        )
