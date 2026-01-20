import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import AIInsight, ReasoningRow
from app.models.prompts import CategoryDefinition, FewShotExample


class AnalysisAgent:
    def __init__(self, llm: BaseChatModel, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt

    def analyze(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
    ) -> AIInsight:
        prompt = self._build_prompt(categories, few_shots, article_content)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
    ) -> str:
        parts = [self.system_prompt, "\n\n## Category Definitions\n"]

        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n")

        if few_shots:
            parts.append("\n## Examples\n")
            for ex in few_shots:
                parts.append(f"**News:** {ex.news_content}\n")
                parts.append(f"**Category:** {ex.category}\n")
                parts.append(f"**Reasoning:** {ex.reasoning}\n\n")

        parts.append("\n## Article to Analyze\n")
        parts.append(article_content)
        parts.append("\n\n## Instructions\n")
        parts.append("Respond with a JSON object containing:\n")
        parts.append("- category: the category name\n")
        parts.append("- reasoning_table: array of {category_excerpt, news_excerpt, reasoning}\n")
        parts.append("- confidence: float between 0 and 1\n")

        return "".join(parts)

    def _parse_response(self, response: str) -> AIInsight:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        return AIInsight(
            category=data["category"],
            reasoning_table=[
                ReasoningRow(**row) for row in data["reasoning_table"]
            ],
            confidence=data["confidence"],
        )
