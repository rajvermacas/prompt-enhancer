"""Tests for ChangeRequestService."""

import json
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def org_workspace_dir(tmp_path):
    """Create an organization workspace directory with prompts and change_requests dir."""
    org_dir = tmp_path / "workspaces" / "organization"
    org_dir.mkdir(parents=True)
    change_requests_dir = org_dir / "change_requests"
    change_requests_dir.mkdir()

    # Create initial prompt files
    with open(org_dir / "category_definitions.json", "w") as f:
        json.dump({"categories": [{"name": "Tech", "definition": "Technology news"}]}, f)
    with open(org_dir / "few_shot_examples.json", "w") as f:
        json.dump({"examples": []}, f)
    with open(org_dir / "system_prompt.json", "w") as f:
        json.dump({"content": "Original system prompt"}, f)

    return tmp_path / "workspaces"


def test_create_change_request(org_workspace_dir):
    """ChangeRequestService creates a new pending change request."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)
    change_request = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": [{"name": "Tech", "definition": "Updated tech"}]},
        description="Updating tech category",
    )

    assert change_request.id.startswith("cr-")
    assert change_request.submitted_by == "u-test"
    assert change_request.prompt_type == PromptType.CATEGORY_DEFINITIONS
    assert change_request.status == ChangeRequestStatus.PENDING
    assert change_request.proposed_content == {
        "categories": [{"name": "Tech", "definition": "Updated tech"}]
    }
    assert change_request.current_content == {
        "categories": [{"name": "Tech", "definition": "Technology news"}]
    }
    assert change_request.description == "Updating tech category"


def test_get_change_request(org_workspace_dir):
    """ChangeRequestService retrieves a change request by ID."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)
    created = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": [{"id": "ex-1", "content": "test"}]},
    )

    retrieved = service.get_change_request(created.id)

    assert retrieved.id == created.id
    assert retrieved.submitted_by == "u-test"
    assert retrieved.prompt_type == PromptType.FEW_SHOTS


def test_get_change_request_not_found(org_workspace_dir):
    """ChangeRequestService raises error when change request not found."""
    from app.services.change_request_service import (
        ChangeRequestNotFoundError,
        ChangeRequestService,
    )

    service = ChangeRequestService(org_workspace_dir)

    with pytest.raises(ChangeRequestNotFoundError):
        service.get_change_request("cr-nonexistent")


def test_list_change_requests(org_workspace_dir):
    """ChangeRequestService lists all change requests sorted by submitted_at desc."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    # Create change requests (need different user_ids to avoid duplicate pending error)
    cr1 = service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )
    cr2 = service.create_change_request(
        user_id="u-user2",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )
    cr3 = service.create_change_request(
        user_id="u-user3",
        prompt_type=PromptType.SYSTEM_PROMPT,
        proposed_content={"content": "new prompt"},
    )

    all_requests = service.list_change_requests()

    assert len(all_requests) == 3
    # Should be sorted by submitted_at desc (most recent first)
    assert all_requests[0].id == cr3.id
    assert all_requests[1].id == cr2.id
    assert all_requests[2].id == cr1.id


def test_list_change_requests_filter_by_status(org_workspace_dir):
    """ChangeRequestService filters change requests by status."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    # Create and process change requests
    cr1 = service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )
    cr2 = service.create_change_request(
        user_id="u-user2",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )
    # Reject one request
    service.reject_change_request(cr1.id, reviewer_id="r-admin")

    pending_requests = service.list_change_requests(status=ChangeRequestStatus.PENDING)
    rejected_requests = service.list_change_requests(status=ChangeRequestStatus.REJECTED)

    assert len(pending_requests) == 1
    assert pending_requests[0].id == cr2.id
    assert len(rejected_requests) == 1
    assert rejected_requests[0].id == cr1.id


def test_approve_change_request(org_workspace_dir):
    """ChangeRequestService approves request and updates the prompt file."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    new_categories = {"categories": [{"name": "Tech", "definition": "Updated tech news"}]}
    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content=new_categories,
    )

    approved = service.approve_change_request(
        cr.id, reviewer_id="r-admin", feedback="Looks good!"
    )

    assert approved.status == ChangeRequestStatus.APPROVED
    assert approved.reviewed_by == "r-admin"
    assert approved.review_feedback == "Looks good!"
    assert approved.reviewed_at is not None

    # Verify the prompt file was updated
    with open(org_workspace_dir / "organization" / "category_definitions.json") as f:
        saved_content = json.load(f)
    assert saved_content == new_categories


def test_approve_change_request_conflict(org_workspace_dir):
    """ChangeRequestService raises conflict error when content changed since snapshot."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestConflictError,
        ChangeRequestService,
    )

    service = ChangeRequestService(org_workspace_dir)

    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": [{"name": "New", "definition": "New cat"}]},
    )

    # Simulate external change to the file
    with open(org_workspace_dir / "organization" / "category_definitions.json", "w") as f:
        json.dump({"categories": [{"name": "Changed", "definition": "External change"}]}, f)

    with pytest.raises(ChangeRequestConflictError):
        service.approve_change_request(cr.id, reviewer_id="r-admin")


def test_reject_change_request(org_workspace_dir):
    """ChangeRequestService rejects a change request."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )

    rejected = service.reject_change_request(
        cr.id, reviewer_id="r-admin", feedback="Needs more examples"
    )

    assert rejected.status == ChangeRequestStatus.REJECTED
    assert rejected.reviewed_by == "r-admin"
    assert rejected.review_feedback == "Needs more examples"
    assert rejected.reviewed_at is not None


def test_revise_change_request(org_workspace_dir):
    """ChangeRequestService allows revising a rejected request."""
    from app.models.change_request import ChangeRequestStatus, PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    # Create and reject a request
    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )
    service.reject_change_request(cr.id, reviewer_id="r-admin", feedback="Needs examples")

    # Revise the request
    revised = service.revise_change_request(
        cr.id,
        proposed_content={"examples": [{"id": "ex-1", "content": "new example"}]},
        description="Added examples as requested",
    )

    assert revised.status == ChangeRequestStatus.PENDING
    assert revised.proposed_content == {
        "examples": [{"id": "ex-1", "content": "new example"}]
    }
    assert revised.description == "Added examples as requested"
    # Review info should be cleared
    assert revised.reviewed_by is None
    assert revised.reviewed_at is None
    assert revised.review_feedback is None


def test_revise_non_rejected_request_fails(org_workspace_dir):
    """ChangeRequestService prevents revising non-rejected requests."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        InvalidChangeRequestStateError,
    )

    service = ChangeRequestService(org_workspace_dir)

    # Create a pending request (not rejected)
    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )

    with pytest.raises(InvalidChangeRequestStateError):
        service.revise_change_request(
            cr.id,
            proposed_content={"examples": [{"id": "ex-1", "content": "new"}]},
        )


def test_withdraw_change_request(org_workspace_dir):
    """ChangeRequestService withdraws (deletes) a pending request."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestNotFoundError,
        ChangeRequestService,
    )

    service = ChangeRequestService(org_workspace_dir)

    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.SYSTEM_PROMPT,
        proposed_content={"content": "new prompt"},
    )

    service.withdraw_change_request(cr.id)

    # Request should no longer exist
    with pytest.raises(ChangeRequestNotFoundError):
        service.get_change_request(cr.id)


def test_withdraw_non_pending_request_fails(org_workspace_dir):
    """ChangeRequestService prevents withdrawing non-pending requests."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        InvalidChangeRequestStateError,
    )

    service = ChangeRequestService(org_workspace_dir)

    cr = service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )
    # Reject it first
    service.reject_change_request(cr.id, reviewer_id="r-admin")

    with pytest.raises(InvalidChangeRequestStateError):
        service.withdraw_change_request(cr.id)


def test_has_pending_request_for_prompt_type(org_workspace_dir):
    """ChangeRequestService checks if user has pending request for prompt type."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    # No pending request initially
    assert service.has_pending_request("u-test", PromptType.CATEGORY_DEFINITIONS) is False

    # Create a pending request
    service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )

    # Now should have pending request
    assert service.has_pending_request("u-test", PromptType.CATEGORY_DEFINITIONS) is True
    # Different prompt type should not have pending request
    assert service.has_pending_request("u-test", PromptType.FEW_SHOTS) is False
    # Different user should not have pending request
    assert service.has_pending_request("u-other", PromptType.CATEGORY_DEFINITIONS) is False


def test_count_pending_requests(org_workspace_dir):
    """ChangeRequestService counts all pending requests."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import ChangeRequestService

    service = ChangeRequestService(org_workspace_dir)

    assert service.count_pending_requests() == 0

    # Create pending requests
    service.create_change_request(
        user_id="u-user1",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )
    service.create_change_request(
        user_id="u-user2",
        prompt_type=PromptType.FEW_SHOTS,
        proposed_content={"examples": []},
    )

    assert service.count_pending_requests() == 2

    # Reject one - should decrease count
    requests = service.list_change_requests()
    service.reject_change_request(requests[0].id, reviewer_id="r-admin")

    assert service.count_pending_requests() == 1


def test_create_change_request_duplicate_pending_fails(org_workspace_dir):
    """ChangeRequestService prevents duplicate pending requests from same user."""
    from app.models.change_request import PromptType
    from app.services.change_request_service import (
        ChangeRequestService,
        DuplicatePendingRequestError,
    )

    service = ChangeRequestService(org_workspace_dir)

    # Create first pending request
    service.create_change_request(
        user_id="u-test",
        prompt_type=PromptType.CATEGORY_DEFINITIONS,
        proposed_content={"categories": []},
    )

    # Try to create another pending request for same user and prompt type
    with pytest.raises(DuplicatePendingRequestError):
        service.create_change_request(
            user_id="u-test",
            prompt_type=PromptType.CATEGORY_DEFINITIONS,
            proposed_content={"categories": [{"name": "New", "definition": "New cat"}]},
        )
