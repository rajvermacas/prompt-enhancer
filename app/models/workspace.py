from datetime import datetime

from pydantic import BaseModel


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
