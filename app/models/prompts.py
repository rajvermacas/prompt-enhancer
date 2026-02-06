from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CategoryDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    definition: str


class FewShotExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    news_content: str
    category: str
    reasoning: str


class PromptConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[CategoryDefinition]


class FewShotConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    examples: list[FewShotExample]


class SystemPromptConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str


class VersionedPromptConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    categories: list[CategoryDefinition]


class VersionedFewShotConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    examples: list[FewShotExample]


class VersionedSystemPromptConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    content: str


class RestorePromptVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)


class PromptHistoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    updated_at: datetime
    updated_by: str
    source: str
    change_request_id: str | None
    content: dict[str, Any]
