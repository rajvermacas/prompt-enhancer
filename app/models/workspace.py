from datetime import datetime

from pydantic import BaseModel

from app.models.news import NewsSource


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    user_id: str | None
    created_at: datetime
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE
    is_organization: bool = False
