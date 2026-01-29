import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import UserNotFoundError
from app.dependencies import (
    get_change_request_service,
    get_current_user_or_redirect,
    get_user_service,
    get_workspace_service,
)
from app.models.auth import User, UserRole
from app.models.change_request import ChangeRequestStatus
from app.services.change_request_service import (
    ChangeRequestNotFoundError,
    ChangeRequestService,
)
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def news_list_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    pending_count = change_request_service.count_pending_requests()
    return templates.TemplateResponse(
        "news_list.html",
        {
            "request": request,
            "workspaces": workspaces,
            "current_user": current_user,
            "pending_count": pending_count,
        },
    )


@router.get("/prompts", response_class=HTMLResponse)
def prompts_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    pending_count = change_request_service.count_pending_requests()
    return templates.TemplateResponse(
        "prompts.html",
        {
            "request": request,
            "workspaces": workspaces,
            "current_user": current_user,
            "pending_count": pending_count,
        },
    )


@router.get("/approvals", response_class=HTMLResponse)
def approvals_page(
    request: Request,
    status: str | None = None,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
    user_service: UserService = Depends(get_user_service),
):
    """Approvals queue page."""
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    pending_count = change_request_service.count_pending_requests()

    # Filter by status if provided
    status_filter = None
    if status:
        status_filter = ChangeRequestStatus(status)

    change_requests = change_request_service.list_change_requests(status=status_filter)

    # Build submitter_emails dict for display
    submitter_emails = _build_user_email_map(change_requests, user_service)

    # Determine current filter for tab highlighting
    current_filter = status if status else "all"

    return templates.TemplateResponse(
        "approvals.html",
        {
            "request": request,
            "workspaces": workspaces,
            "current_user": current_user,
            "change_requests": change_requests,
            "pending_count": pending_count,
            "submitter_emails": submitter_emails,
            "current_filter": current_filter,
        },
    )


@router.get("/approvals/{request_id}", response_class=HTMLResponse)
def approval_detail_page(
    request: Request,
    request_id: str,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
    user_service: UserService = Depends(get_user_service),
):
    """Approval detail page with diff view."""
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    pending_count = change_request_service.count_pending_requests()

    try:
        change_request = change_request_service.get_change_request(request_id)
    except ChangeRequestNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")

    # Format JSON for display
    current_content_json = json.dumps(change_request.current_content, indent=2)
    proposed_content_json = json.dumps(change_request.proposed_content, indent=2)

    # Get submitter email
    submitter_email = _get_user_email(change_request.submitted_by, user_service)

    # Get reviewer email if exists
    reviewer_email = None
    if change_request.reviewed_by:
        reviewer_email = _get_user_email(change_request.reviewed_by, user_service)

    return templates.TemplateResponse(
        "approval_detail.html",
        {
            "request": request,
            "workspaces": workspaces,
            "current_user": current_user,
            "change_request": change_request,
            "pending_count": pending_count,
            "submitter_email": submitter_email,
            "reviewer_email": reviewer_email,
            "current_content_json": current_content_json,
            "proposed_content_json": proposed_content_json,
            "is_approver": current_user.role == UserRole.APPROVER,
            "is_own_request": change_request.submitted_by == current_user.id,
        },
    )


def _get_user_email(user_id: str, user_service: UserService) -> str:
    """Get user email by ID, returning the user_id if not found."""
    try:
        user = user_service.get_user(user_id)
        return user.email
    except UserNotFoundError:
        return user_id


def _build_user_email_map(change_requests: list, user_service: UserService) -> dict:
    """Build a dictionary mapping user_id to email for all submitters."""
    user_ids = {cr.submitted_by for cr in change_requests}
    email_map = {}
    for user_id in user_ids:
        email_map[user_id] = _get_user_email(user_id, user_service)
    return email_map


@router.get("/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    user_service: UserService = Depends(get_user_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    """User management page. Approver only."""
    if current_user.role != UserRole.APPROVER:
        raise HTTPException(status_code=403, detail="Approver access required")

    users = user_service.list_users()
    pending_count = change_request_service.count_pending_requests()

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "current_user": current_user,
            "users": users,
            "pending_count": pending_count,
        },
    )
