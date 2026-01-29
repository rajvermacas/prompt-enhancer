"""API routes for change request management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_change_request_service,
    get_current_approver,
    get_current_user,
)
from app.models.auth import User
from app.models.change_request import (
    ChangeRequest,
    ChangeRequestStatus,
    CreateChangeRequestInput,
    ReviewChangeRequestInput,
    ReviseChangeRequestInput,
)
from app.services.change_request_service import (
    ChangeRequestConflictError,
    ChangeRequestNotFoundError,
    ChangeRequestService,
    DuplicatePendingRequestError,
    InvalidChangeRequestStateError,
)

router = APIRouter(prefix="/change-requests", tags=["change-requests"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ChangeRequest)
def create_change_request(
    body: CreateChangeRequestInput,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> ChangeRequest:
    """Submit a new change request.

    Returns 409 if the user already has a pending request for the same prompt type.
    """
    try:
        return service.create_change_request(
            user_id=current_user.id,
            prompt_type=body.prompt_type,
            proposed_content=body.proposed_content,
            description=body.description,
        )
    except DuplicatePendingRequestError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a pending request for {e.prompt_type.value}",
        )


@router.get("", response_model=list[ChangeRequest])
def list_change_requests(
    status_filter: ChangeRequestStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> list[ChangeRequest]:
    """List all change requests, optionally filtered by status."""
    return service.list_change_requests(status=status_filter)


@router.get("/{request_id}", response_model=ChangeRequest)
def get_change_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> ChangeRequest:
    """Get a single change request by ID."""
    try:
        return service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )


@router.post("/{request_id}/approve", response_model=ChangeRequest)
def approve_change_request(
    request_id: str,
    body: ReviewChangeRequestInput,
    current_user: User = Depends(get_current_approver),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> ChangeRequest:
    """Approve a change request and apply the changes.

    Only approvers can approve requests.
    Cannot approve your own request.
    Returns 409 if the underlying content has changed since the request was created.
    """
    try:
        change_request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )

    # Cannot approve own request
    if change_request.submitted_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve your own request",
        )

    # Check if already processed
    if change_request.status != ChangeRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Request is already {change_request.status.value}",
        )

    try:
        return service.approve_change_request(
            request_id=request_id,
            reviewer_id=current_user.id,
            feedback=body.feedback,
        )
    except ChangeRequestConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/{request_id}/reject", response_model=ChangeRequest)
def reject_change_request(
    request_id: str,
    body: ReviewChangeRequestInput,
    current_user: User = Depends(get_current_approver),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> ChangeRequest:
    """Reject a change request.

    Only approvers can reject requests.
    """
    try:
        return service.reject_change_request(
            request_id=request_id,
            reviewer_id=current_user.id,
            feedback=body.feedback,
        )
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )


@router.post("/{request_id}/revise", response_model=ChangeRequest)
def revise_change_request(
    request_id: str,
    body: ReviseChangeRequestInput,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> ChangeRequest:
    """Revise a rejected change request.

    Only the original submitter can revise their request.
    Only rejected requests can be revised.
    """
    try:
        change_request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )

    # Only original submitter can revise
    if change_request.submitted_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original submitter can revise this request",
        )

    try:
        return service.revise_change_request(
            request_id=request_id,
            proposed_content=body.proposed_content,
            description=body.description,
        )
    except InvalidChangeRequestStateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only rejected requests can be revised",
        )


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_change_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    service: ChangeRequestService = Depends(get_change_request_service),
) -> None:
    """Withdraw (delete) a pending change request.

    Only the original submitter can withdraw their request.
    Only pending requests can be withdrawn.
    """
    try:
        change_request = service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found",
        )

    # Only original submitter can withdraw
    if change_request.submitted_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the original submitter can withdraw this request",
        )

    try:
        service.withdraw_change_request(request_id)
    except InvalidChangeRequestStateError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be withdrawn",
        )
