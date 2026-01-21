from datetime import datetime

from pydantic import BaseModel

from app.models.news import NewsSource


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE
