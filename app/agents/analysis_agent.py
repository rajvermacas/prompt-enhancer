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
        insight = self._parse_response(response.content)

        allowed_categories = {cat.name for cat in categories}
        if insight.category not in allowed_categories:
            coerced = self._coerce_category_from_excerpt(insight, categories)
            if coerced:
                insight.category = coerced
            else:
                raise ValueError(
                    f"LLM returned category '{insight.category}' not in allowed set"
                )

        return insight

    def _build_prompt(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
    ) -> str:
        parts = ["## Category Definitions\n"]

        parts.append(
            "CRITICAL: Category names may be arbitrary or misleading. "
            "You MUST classify based ONLY on the definition text, NOT the category name. "
            "Match the news content against each definition and select the category "
            "whose DEFINITION best describes the content.\n\n"
        )

        for cat in categories:
            parts.append(f"### {cat.name}\n")
            parts.append(f"**Definition (use this for classification):** {cat.definition}\n\n")

        allowed = [cat.name for cat in categories]
        parts.append("Allowed category names for output (must match exactly):\n")
        for name in allowed:
            parts.append(f"- {name}\n")

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
        parts.append(
            "\nRules:\n"
            "- IGNORE category names when deciding classification - use ONLY the definition text\n"
            "- category MUST be one of the Allowed category names listed above (exact match)\n"
            "- category_excerpt MUST be verbatim from the chosen category definition\n"
            "- If the news is semantically neutral but a category is DEFINED as 'neutral news', "
            "select that category regardless of what the category is named\n"
        )

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

    def _coerce_category_from_excerpt(
        self,
        insight: AIInsight,
        categories: list[CategoryDefinition],
    ) -> str | None:
        if not insight.reasoning_table:
            return None

        best_category: str | None = None
        best_score = 0
        tie = False

        for cat in categories:
            definition = cat.definition or ""
            if not definition:
                continue

            score_for_cat = 0
            for row in insight.reasoning_table:
                excerpt = (row.category_excerpt or "").strip()
                if not excerpt:
                    continue
                if excerpt in definition:
                    score_for_cat = max(score_for_cat, len(excerpt))

            if score_for_cat > best_score:
                best_score = score_for_cat
                best_category = cat.name
                tie = False
            elif score_for_cat == best_score and score_for_cat != 0:
                tie = True

        if tie or best_score == 0:
            return None
        return best_category
