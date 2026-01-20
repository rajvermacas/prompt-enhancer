import json
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import (
    EvaluationReport,
    Feedback,
    FewShotGap,
    PromptGap,
)
from app.models.prompts import CategoryDefinition, FewShotExample


EVALUATION_SYSTEM_PROMPT = """You are a prompt evaluation expert. Your task is to analyze why an AI classification was correct or incorrect, and identify gaps in the prompt configuration.

Analyze the provided feedback and identify:
1. What caused the correct/incorrect classification
2. Gaps or issues in category definitions
3. Gaps or issues in few-shot examples

Respond with a JSON object containing:
- diagnosis: string explaining what went right/wrong
- prompt_gaps: array of {location, issue, suggestion}
- few_shot_gaps: array of {example_id, issue, suggestion}
- summary: concise actionable summary for the user
"""


class EvaluationAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def evaluate(
        self,
        feedback: Feedback,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> EvaluationReport:
        prompt = self._build_prompt(feedback, categories, few_shots)
        messages = [
            SystemMessage(content=EVALUATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(feedback.id, response.content)

    def _build_prompt(
        self,
        feedback: Feedback,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## Feedback Details\n"]
        parts.append(f"- Thumbs up: {feedback.thumbs_up}\n")
        parts.append(f"- AI predicted: {feedback.ai_insight.category}\n")
        parts.append(f"- Correct category: {feedback.correct_category}\n")
        parts.append(f"- User reasoning: {feedback.reasoning}\n\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"- ID: {ex.id}, Category: {ex.category}\n")
                parts.append(f"  Content: {ex.news_content[:100]}...\n\n")

        return "".join(parts)

    def _parse_response(self, feedback_id: str, response: str) -> EvaluationReport:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        return EvaluationReport(
            id=f"rpt-{uuid.uuid4().hex[:8]}",
            feedback_id=feedback_id,
            diagnosis=data["diagnosis"],
            prompt_gaps=[PromptGap(**gap) for gap in data.get("prompt_gaps", [])],
            few_shot_gaps=[FewShotGap(**gap) for gap in data.get("few_shot_gaps", [])],
            summary=data["summary"],
        )
