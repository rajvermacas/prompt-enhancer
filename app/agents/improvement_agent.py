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
        return ImprovementSuggestion(
            category_suggestions=data.get("category_suggestions", []),
            few_shot_suggestions=data.get("few_shot_suggestions", []),
            priority_order=data.get("priority_order", []),
            updated_categories=data.get("updated_categories", []),
            updated_few_shots=data.get("updated_few_shots", []),
        )
