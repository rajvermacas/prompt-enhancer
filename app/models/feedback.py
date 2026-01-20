from datetime import datetime

from pydantic import BaseModel


class ReasoningRow(BaseModel):
    category_excerpt: str
    news_excerpt: str
    reasoning: str


class AIInsight(BaseModel):
    category: str
    reasoning_table: list[ReasoningRow]
    confidence: float


class Feedback(BaseModel):
    id: str
    article_id: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    note: str
    ai_insight: AIInsight
    created_at: datetime


class PromptGap(BaseModel):
    location: str
    issue: str
    suggestion: str


class FewShotGap(BaseModel):
    example_id: str
    issue: str
    suggestion: str


class EvaluationReport(BaseModel):
    id: str
    feedback_id: str
    diagnosis: str
    prompt_gaps: list[PromptGap]
    few_shot_gaps: list[FewShotGap]
    summary: str


class ImprovementSuggestion(BaseModel):
    category_suggestions: list[dict]
    few_shot_suggestions: list[dict]
    priority_order: list[str]
