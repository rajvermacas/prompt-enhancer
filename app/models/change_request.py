from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class PromptType(str, Enum):
    CATEGORY_DEFINITIONS = "CATEGORY_DEFINITIONS"
    FEW_SHOTS = "FEW_SHOTS"
    SYSTEM_PROMPT = "SYSTEM_PROMPT"


class ChangeRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChangeRequest(BaseModel):
    id: str
    workspace_id: str
    prompt_type: PromptType
    submitted_by: str
    submitted_at: datetime
    status: ChangeRequestStatus
    current_content: dict[str, Any]
    proposed_content: dict[str, Any]
    description: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_feedback: str | None = None


class CreateChangeRequestInput(BaseModel):
    prompt_type: PromptType
    proposed_content: dict[str, Any]
    description: str | None = None


class ReviewChangeRequestInput(BaseModel):
    feedback: str | None = None


class ReviseChangeRequestInput(BaseModel):
    proposed_content: dict[str, Any]
    description: str | None = None
