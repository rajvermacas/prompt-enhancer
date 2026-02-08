from datetime import datetime

from pydantic import BaseModel

from app.models.feedback import AIInsightWithUserAnalysis


class AnalysisRunEntry(BaseModel):
    id: str
    workspace_id: str
    article_id: str
    triggered_user_id: str
    insight: AIInsightWithUserAnalysis
    created_at: datetime


class AnalysisHistoryPage(BaseModel):
    items: list[AnalysisRunEntry]
    total: int
    page: int
    limit: int
    has_next: bool
