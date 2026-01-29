"""Service for managing change requests in the approval workflow."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.change_request import (
    ChangeRequest,
    ChangeRequestStatus,
    PromptType,
)


# Mapping from PromptType to the corresponding file name
PROMPT_TYPE_TO_FILE: dict[PromptType, str] = {
    PromptType.CATEGORY_DEFINITIONS: "category_definitions.json",
    PromptType.FEW_SHOTS: "few_shot_examples.json",
    PromptType.SYSTEM_PROMPT: "system_prompt.json",
}


class ChangeRequestNotFoundError(Exception):
    """Raised when a change request is not found."""

    def __init__(self, request_id: str):
        self.request_id = request_id
        super().__init__(f"Change request not found: {request_id}")


class ChangeRequestConflictError(Exception):
    """Raised when there's a conflict during approval (content changed)."""

    def __init__(self, request_id: str, message: str):
        self.request_id = request_id
        super().__init__(f"Conflict for change request {request_id}: {message}")


class InvalidChangeRequestStateError(Exception):
    """Raised when an operation is invalid for the current request state."""

    def __init__(self, request_id: str, current_status: ChangeRequestStatus, operation: str):
        self.request_id = request_id
        self.current_status = current_status
        self.operation = operation
        super().__init__(
            f"Cannot {operation} change request {request_id}: "
            f"current status is {current_status.value}"
        )


class DuplicatePendingRequestError(Exception):
    """Raised when user tries to create duplicate pending request for same prompt type."""

    def __init__(self, user_id: str, prompt_type: PromptType):
        self.user_id = user_id
        self.prompt_type = prompt_type
        super().__init__(
            f"User {user_id} already has a pending request for {prompt_type.value}"
        )


class ChangeRequestService:
    """Service for managing change requests."""

    ORGANIZATION_WORKSPACE_ID = "organization"

    def __init__(self, workspaces_path: str | Path):
        self.workspaces_path = Path(workspaces_path)
        self.org_workspace_path = self.workspaces_path / self.ORGANIZATION_WORKSPACE_ID
        self.change_requests_dir = self.org_workspace_path / "change_requests"
        # Ensure directories exist
        self.change_requests_dir.mkdir(parents=True, exist_ok=True)

    def create_change_request(
        self,
        user_id: str,
        prompt_type: PromptType,
        proposed_content: dict[str, Any],
        description: str | None = None,
    ) -> ChangeRequest:
        """Create a new pending change request.

        Args:
            user_id: The ID of the user submitting the request.
            prompt_type: The type of prompt being changed.
            proposed_content: The proposed new content.
            description: Optional description of the change.

        Returns:
            The created ChangeRequest.

        Raises:
            DuplicatePendingRequestError: If user has pending request for same prompt type.
        """
        # Check for duplicate pending request
        if self.has_pending_request(user_id, prompt_type):
            raise DuplicatePendingRequestError(user_id, prompt_type)

        request_id = f"cr-{uuid.uuid4().hex[:8]}"
        current_content = self._load_current_content(prompt_type)

        change_request = ChangeRequest(
            id=request_id,
            workspace_id=self.ORGANIZATION_WORKSPACE_ID,
            prompt_type=prompt_type,
            submitted_by=user_id,
            submitted_at=datetime.now(),
            status=ChangeRequestStatus.PENDING,
            current_content=current_content,
            proposed_content=proposed_content,
            description=description,
        )

        self._save_change_request(change_request)
        return change_request

    def get_change_request(self, request_id: str) -> ChangeRequest:
        """Get a change request by ID.

        Args:
            request_id: The ID of the change request.

        Returns:
            The ChangeRequest.

        Raises:
            ChangeRequestNotFoundError: If request not found.
        """
        request_file = self.change_requests_dir / f"{request_id}.json"
        if not request_file.exists():
            raise ChangeRequestNotFoundError(request_id)

        with open(request_file) as f:
            data = json.load(f)
        return ChangeRequest.model_validate(data)

    def list_change_requests(
        self, status: ChangeRequestStatus | None = None
    ) -> list[ChangeRequest]:
        """List all change requests, optionally filtered by status.

        Args:
            status: Optional status to filter by.

        Returns:
            List of ChangeRequests sorted by submitted_at descending.
        """
        requests: list[ChangeRequest] = []
        for request_file in self.change_requests_dir.glob("*.json"):
            with open(request_file) as f:
                data = json.load(f)
            change_request = ChangeRequest.model_validate(data)
            if status is None or change_request.status == status:
                requests.append(change_request)

        # Sort by submitted_at descending (most recent first)
        return sorted(requests, key=lambda r: r.submitted_at, reverse=True)

    def approve_change_request(
        self,
        request_id: str,
        reviewer_id: str,
        feedback: str | None = None,
    ) -> ChangeRequest:
        """Approve a change request and apply the changes.

        Args:
            request_id: The ID of the change request.
            reviewer_id: The ID of the reviewer.
            feedback: Optional feedback.

        Returns:
            The updated ChangeRequest.

        Raises:
            ChangeRequestNotFoundError: If request not found.
            ChangeRequestConflictError: If content changed since snapshot.
        """
        change_request = self.get_change_request(request_id)

        # Check for conflict - current content may have changed
        current_content = self._load_current_content(change_request.prompt_type)
        if current_content != change_request.current_content:
            raise ChangeRequestConflictError(
                request_id,
                "The prompt content has changed since this request was created. "
                "Please review the changes and create a new request.",
            )

        # Apply the changes to the prompt file
        self._save_prompt_content(change_request.prompt_type, change_request.proposed_content)

        # Update the change request status
        change_request.status = ChangeRequestStatus.APPROVED
        change_request.reviewed_by = reviewer_id
        change_request.reviewed_at = datetime.now()
        change_request.review_feedback = feedback

        self._save_change_request(change_request)
        return change_request

    def reject_change_request(
        self,
        request_id: str,
        reviewer_id: str,
        feedback: str | None = None,
    ) -> ChangeRequest:
        """Reject a change request.

        Args:
            request_id: The ID of the change request.
            reviewer_id: The ID of the reviewer.
            feedback: Optional feedback.

        Returns:
            The updated ChangeRequest.

        Raises:
            ChangeRequestNotFoundError: If request not found.
        """
        change_request = self.get_change_request(request_id)

        change_request.status = ChangeRequestStatus.REJECTED
        change_request.reviewed_by = reviewer_id
        change_request.reviewed_at = datetime.now()
        change_request.review_feedback = feedback

        self._save_change_request(change_request)
        return change_request

    def revise_change_request(
        self,
        request_id: str,
        proposed_content: dict[str, Any],
        description: str | None = None,
    ) -> ChangeRequest:
        """Revise a rejected change request.

        Args:
            request_id: The ID of the change request.
            proposed_content: The revised proposed content.
            description: Optional updated description.

        Returns:
            The updated ChangeRequest.

        Raises:
            ChangeRequestNotFoundError: If request not found.
            InvalidChangeRequestStateError: If request is not in REJECTED state.
        """
        change_request = self.get_change_request(request_id)

        if change_request.status != ChangeRequestStatus.REJECTED:
            raise InvalidChangeRequestStateError(
                request_id, change_request.status, "revise"
            )

        # Refresh the snapshot of current content
        current_content = self._load_current_content(change_request.prompt_type)

        change_request.status = ChangeRequestStatus.PENDING
        change_request.proposed_content = proposed_content
        change_request.current_content = current_content
        change_request.description = description
        # Clear review info
        change_request.reviewed_by = None
        change_request.reviewed_at = None
        change_request.review_feedback = None

        self._save_change_request(change_request)
        return change_request

    def withdraw_change_request(self, request_id: str) -> None:
        """Withdraw (delete) a pending change request.

        Args:
            request_id: The ID of the change request.

        Raises:
            ChangeRequestNotFoundError: If request not found.
            InvalidChangeRequestStateError: If request is not in PENDING state.
        """
        change_request = self.get_change_request(request_id)

        if change_request.status != ChangeRequestStatus.PENDING:
            raise InvalidChangeRequestStateError(
                request_id, change_request.status, "withdraw"
            )

        request_file = self.change_requests_dir / f"{request_id}.json"
        request_file.unlink()

    def has_pending_request(self, user_id: str, prompt_type: PromptType) -> bool:
        """Check if user has a pending request for the given prompt type.

        Args:
            user_id: The ID of the user.
            prompt_type: The type of prompt.

        Returns:
            True if user has pending request for the prompt type.
        """
        for request_file in self.change_requests_dir.glob("*.json"):
            with open(request_file) as f:
                data = json.load(f)
            change_request = ChangeRequest.model_validate(data)
            if (
                change_request.submitted_by == user_id
                and change_request.prompt_type == prompt_type
                and change_request.status == ChangeRequestStatus.PENDING
            ):
                return True
        return False

    def count_pending_requests(self) -> int:
        """Count all pending change requests.

        Returns:
            The number of pending requests.
        """
        count = 0
        for request_file in self.change_requests_dir.glob("*.json"):
            with open(request_file) as f:
                data = json.load(f)
            change_request = ChangeRequest.model_validate(data)
            if change_request.status == ChangeRequestStatus.PENDING:
                count += 1
        return count

    def _load_current_content(self, prompt_type: PromptType) -> dict[str, Any]:
        """Load the current content for the given prompt type."""
        filename = PROMPT_TYPE_TO_FILE[prompt_type]
        filepath = self.org_workspace_path / filename
        if not filepath.exists():
            # Return empty structure based on prompt type
            return self._get_empty_content_for_type(prompt_type)
        with open(filepath) as f:
            return json.load(f)

    def _get_empty_content_for_type(self, prompt_type: PromptType) -> dict[str, Any]:
        """Return empty content structure for the given prompt type."""
        if prompt_type == PromptType.CATEGORY_DEFINITIONS:
            return {"categories": []}
        if prompt_type == PromptType.FEW_SHOTS:
            return {"examples": []}
        if prompt_type == PromptType.SYSTEM_PROMPT:
            return {"content": ""}
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    def _save_prompt_content(
        self, prompt_type: PromptType, content: dict[str, Any]
    ) -> None:
        """Save content to the prompt file."""
        filename = PROMPT_TYPE_TO_FILE[prompt_type]
        filepath = self.org_workspace_path / filename
        with open(filepath, "w") as f:
            json.dump(content, f, indent=2)

    def _save_change_request(self, change_request: ChangeRequest) -> None:
        """Save a change request to disk."""
        request_file = self.change_requests_dir / f"{change_request.id}.json"
        with open(request_file, "w") as f:
            json.dump(change_request.model_dump(mode="json"), f, indent=2)
