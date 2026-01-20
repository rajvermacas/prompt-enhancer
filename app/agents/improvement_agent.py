import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import EvaluationReport, ImprovementSuggestion
from app.models.prompts import CategoryDefinition, FewShotExample


IMPROVEMENT_SYSTEM_PROMPT = """You are a prompt optimization expert. Analyze the evaluation reports and suggest improvements to category definitions and few-shot examples.

Focus on:
1. Patterns across multiple reports
2. Recurring issues in definitions
3. Missing or misleading few-shot examples

Respond with a JSON object containing:
- category_suggestions: array of {category, current, suggested, rationale}
- few_shot_suggestions: array of {action: "add"|"modify"|"remove", details}
- priority_order: array of strings indicating what to fix first
- updated_categories: array of {category, updated_definition} for changed items only
- updated_few_shots: array of {action, example} for changed items only
  - example must include id and full fields for add/modify, id only for remove

Rules:
- Return ONLY valid JSON (no markdown).
- For updated_categories, include only entries with a non-empty updated_definition.
- For updated_few_shots, include add/modify entries only if example has non-empty
  news_content, category, and reasoning.
- If you cannot provide full content for an item, omit it from updated_* arrays.
"""


class ImprovementAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def suggest_improvements(
        self,
        reports: list[EvaluationReport],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> ImprovementSuggestion:
        prompt = self._build_prompt(reports, categories, few_shots)
        messages = [
            SystemMessage(content=IMPROVEMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        reports: list[EvaluationReport],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## Evaluation Reports Summary\n\n"]

        for report in reports:
            parts.append(f"### Report {report.id}\n")
            parts.append(f"- Diagnosis: {report.diagnosis}\n")
            parts.append(f"- Summary: {report.summary}\n")
            if report.prompt_gaps:
                parts.append("- Prompt gaps:\n")
                for gap in report.prompt_gaps:
                    parts.append(f"  - {gap.location}: {gap.issue}\n")
            parts.append("\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"- {ex.id}: {ex.category} - {ex.news_content[:50]}...\n")

        return "".join(parts)

    def _parse_response(self, response: str) -> ImprovementSuggestion:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        few_shot_suggestions = data.get("few_shot_suggestions", [])
        updated_few_shots = data.get("updated_few_shots", [])

        def extract_fields(details: dict) -> dict:
            fields = details.get("fields")
            if isinstance(fields, dict):
                return fields
            return details

        def is_missing(value: object) -> bool:
            if value is None:
                return True
            if isinstance(value, str):
                return value.strip() == ""
            return False

        def build_suggestion_map(items: list) -> dict:
            mapped: dict[str, dict] = {}
            for item in items:
                if not isinstance(item, dict):
                    continue
                action = item.get("action")
                details = item.get("details")
                if not isinstance(details, dict):
                    continue
                fields = extract_fields(details)
                example_id = details.get("id") or item.get("id")
                if not isinstance(example_id, str) or example_id.strip() == "":
                    continue
                mapped[example_id] = {
                    "action": action,
                    "example": {
                        "id": example_id,
                        "news_content": fields.get("news_content") or fields.get("text"),
                        "category": fields.get("category"),
                        "reasoning": fields.get("reasoning") or fields.get("explanation"),
                    },
                }
            return mapped

        if isinstance(updated_few_shots, list):
            suggestion_map = build_suggestion_map(
                few_shot_suggestions if isinstance(few_shot_suggestions, list) else []
            )
            normalized: list[dict] = []
            for item in updated_few_shots:
                if not isinstance(item, dict):
                    continue
                action = item.get("action")
                example = item.get("example")
                if not isinstance(example, dict):
                    example = {}
                example_id = example.get("id") or item.get("id")
                if isinstance(example_id, str) and example_id.strip():
                    example["id"] = example_id
                if action != "remove":
                    news_content = example.get("news_content")
                    category = example.get("category")
                    reasoning = example.get("reasoning")
                    if (
                        is_missing(news_content)
                        or is_missing(category)
                        or is_missing(reasoning)
                    ):
                        fallback = suggestion_map.get(example.get("id"))
                        if fallback:
                            fallback_example = fallback.get("example", {})
                            if is_missing(example.get("news_content")):
                                example["news_content"] = fallback_example.get("news_content")
                            if is_missing(example.get("category")):
                                example["category"] = fallback_example.get("category")
                            if is_missing(example.get("reasoning")):
                                example["reasoning"] = fallback_example.get("reasoning")
                normalized.append({"action": action, "example": example})
            updated_few_shots = normalized
        else:
            updated_few_shots = []

        return ImprovementSuggestion(
            category_suggestions=data.get("category_suggestions", []),
            few_shot_suggestions=few_shot_suggestions,
            priority_order=data.get("priority_order", []),
            updated_categories=data.get("updated_categories", []),
            updated_few_shots=updated_few_shots,
        )
