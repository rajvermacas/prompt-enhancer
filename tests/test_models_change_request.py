import pytest
from datetime import datetime
from typing import Any


def test_prompt_type_enum_values():
    """PromptType enum has CATEGORY_DEFINITIONS, FEW_SHOTS, SYSTEM_PROMPT values."""
    from app.models.change_request import PromptType

    assert PromptType.CATEGORY_DEFINITIONS.value == "CATEGORY_DEFINITIONS"
    assert PromptType.FEW_SHOTS.value == "FEW_SHOTS"
    assert PromptType.SYSTEM_PROMPT.value == "SYSTEM_PROMPT"


def test_change_request_status_enum_values():
    """ChangeRequestStatus enum has PENDING, APPROVED, REJECTED values."""
    from app.models.change_request import ChangeRequestStatus

    assert ChangeRequestStatus.PENDING.value == "PENDING"
    assert ChangeRequestStatus.APPROVED.value == "APPROVED"
    assert ChangeRequestStatus.REJECTED.value == "REJECTED"


def test_change_request_creation():
    """ChangeRequest can be created with all required fields."""
    from app.models.change_request import (
        ChangeRequest,
        ChangeRequestStatus,
        PromptType,
    )

    now = datetime.now()
    current_content: dict[str, Any] = {"categories": []}
    proposed_content: dict[str, Any] = {"categories": [{"name": "Test", "definition": "A test category"}]}

    request = ChangeRequest(
        id="cr-001",
        workspace_id="ws-001",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        submitted_by="u-123",
        submitted_at=now,
        status=ChangeRequestStatus.PENDING,
        current_content=current_content,
        proposed_content=proposed_content,
    )

    assert request.id == "cr-001"
    assert request.workspace_id == "ws-001"
    assert request.prompt_type == PromptType.CATEGORY_DEFINITIONS
    assert request.submitted_by == "u-123"
    assert request.submitted_at == now
    assert request.status == ChangeRequestStatus.PENDING
    assert request.current_content == current_content
    assert request.proposed_content == proposed_content
    assert request.description is None
    assert request.reviewed_by is None
    assert request.reviewed_at is None
    assert request.review_feedback is None


def test_change_request_with_optional_fields():
    """ChangeRequest can be created with all optional fields."""
    from app.models.change_request import (
        ChangeRequest,
        ChangeRequestStatus,
        PromptType,
    )

    submitted_at = datetime.now()
    reviewed_at = datetime.now()

    request = ChangeRequest(
        id="cr-002",
        workspace_id="ws-002",
        prompt_type=PromptType.FEW_SHOTS,
        submitted_by="u-456",
        submitted_at=submitted_at,
        status=ChangeRequestStatus.APPROVED,
        current_content={"examples": []},
        proposed_content={"examples": [{"id": "ex-1", "news_content": "Test", "category": "Cat", "reasoning": "Reason"}]},
        description="Adding new few-shot example",
        reviewed_by="u-789",
        reviewed_at=reviewed_at,
        review_feedback="Looks good!",
    )

    assert request.description == "Adding new few-shot example"
    assert request.reviewed_by == "u-789"
    assert request.reviewed_at == reviewed_at
    assert request.review_feedback == "Looks good!"


def test_change_request_missing_required_field_raises():
    """ChangeRequest raises ValidationError when required field is missing."""
    from pydantic import ValidationError
    from app.models.change_request import ChangeRequest, ChangeRequestStatus, PromptType

    with pytest.raises(ValidationError):
        ChangeRequest(
            id="cr-003",
            workspace_id="ws-003",
            prompt_type=PromptType.SYSTEM_PROMPT,
            submitted_by="u-123",
            submitted_at=datetime.now(),
            status=ChangeRequestStatus.PENDING,
            current_content={"content": "old"},
            # missing proposed_content
        )


def test_create_change_request_input():
    """CreateChangeRequestInput can be created with required fields."""
    from app.models.change_request import CreateChangeRequestInput, PromptType

    input_data = CreateChangeRequestInput(
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": [{"name": "New Category", "definition": "New definition"}]},
    )

    assert input_data.prompt_type == PromptType.CATEGORY_DEFINITIONS
    assert input_data.proposed_content == {"categories": [{"name": "New Category", "definition": "New definition"}]}
    assert input_data.description is None


def test_create_change_request_input_with_description():
    """CreateChangeRequestInput can include optional description."""
    from app.models.change_request import CreateChangeRequestInput, PromptType

    input_data = CreateChangeRequestInput(
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
        description="Adding examples for better categorization",
    )

    assert input_data.description == "Adding examples for better categorization"


def test_create_change_request_input_missing_required_raises():
    """CreateChangeRequestInput raises ValidationError when required field is missing."""
    from pydantic import ValidationError
    from app.models.change_request import CreateChangeRequestInput, PromptType

    with pytest.raises(ValidationError):
        CreateChangeRequestInput(
            prompt_type=PromptType.SYSTEM_PROMPT,
            # missing proposed_content
        )


def test_review_change_request_input():
    """ReviewChangeRequestInput can be created with no fields (feedback is optional)."""
    from app.models.change_request import ReviewChangeRequestInput

    input_data = ReviewChangeRequestInput()

    assert input_data.feedback is None


def test_review_change_request_input_with_feedback():
    """ReviewChangeRequestInput can include optional feedback."""
    from app.models.change_request import ReviewChangeRequestInput

    input_data = ReviewChangeRequestInput(feedback="Please revise the category definition")

    assert input_data.feedback == "Please revise the category definition"


def test_revise_change_request_input():
    """ReviseChangeRequestInput can be created with required fields."""
    from app.models.change_request import ReviseChangeRequestInput

    input_data = ReviseChangeRequestInput(
        proposed_content={"content": "Updated system prompt"},
    )

    assert input_data.proposed_content == {"content": "Updated system prompt"}
    assert input_data.description is None


def test_revise_change_request_input_with_description():
    """ReviseChangeRequestInput can include optional description."""
    from app.models.change_request import ReviseChangeRequestInput

    input_data = ReviseChangeRequestInput(
        proposed_content={"content": "Updated content"},
        description="Revised based on feedback",
    )

    assert input_data.description == "Revised based on feedback"


def test_revise_change_request_input_missing_required_raises():
    """ReviseChangeRequestInput raises ValidationError when required field is missing."""
    from pydantic import ValidationError
    from app.models.change_request import ReviseChangeRequestInput

    with pytest.raises(ValidationError):
        ReviseChangeRequestInput(
            description="Missing the proposed_content",
            # missing proposed_content
        )
