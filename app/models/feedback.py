from datetime import datetime

from pydantic import BaseModel, Field, model_validator


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
    based_on_feedback_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class UpdatedFewShotExample(BaseModel):
    id: str | None = None
    news_content: str | None = None
    category: str | None = None
    reasoning: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: dict) -> dict:
        if isinstance(data, dict):
            # Handle 'article' as alias for 'news_content'
            if "article" in data and "news_content" not in data:
                data["news_content"] = data.pop("article")
        return data


class UpdatedFewShot(BaseModel):
    action: str
    example: UpdatedFewShotExample
    source: str | None = None


class CategorySuggestionItem(BaseModel):
    category: str
    current: str
    suggested: str
    rationale: str
    based_on_feedback_ids: list[str]
    user_reasoning_quotes: list[str]


class FewShotSuggestionItem(BaseModel):
    action: str
    source: str
    based_on_feedback_id: str
    details: dict


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
