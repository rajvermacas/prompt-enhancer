from datetime import datetime

from pydantic import BaseModel, Field


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


class UpdatedCategory(BaseModel):
    category: str
    updated_definition: str


class UpdatedFewShotExample(BaseModel):
    id: str
    news_content: str | None = None
    category: str | None = None
    reasoning: str | None = None


class UpdatedFewShot(BaseModel):
    action: str
    example: UpdatedFewShotExample


class ImprovementSuggestion(BaseModel):
    category_suggestions: list[dict]
    few_shot_suggestions: list[dict]
    priority_order: list[str]
    updated_categories: list[UpdatedCategory] = Field(default_factory=list)
    updated_few_shots: list[UpdatedFewShot] = Field(default_factory=list)


class FeedbackWithHeadline(BaseModel):
    id: str
    article_id: str
    article_headline: str
    article_content: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    ai_insight: AIInsight
    created_at: datetime


class ImprovementSuggestionResponse(BaseModel):
    suggestions: ImprovementSuggestion
    feedbacks: list[FeedbackWithHeadline]
