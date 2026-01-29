"""User management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.db import UserNotFoundError
from app.dependencies import (
    get_current_approver,
    get_current_user,
    get_user_service,
)
from app.models.auth import User, UserRole
from app.services.user_service import LastApproverError, UserService


router = APIRouter(prefix="/users", tags=["users"])


class UpdateRoleRequest(BaseModel):
    role: UserRole


@router.get("/me", response_model=User)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return the current authenticated user's information."""
    return current_user


@router.get("", response_model=list[User])
def list_users(
    current_user: User = Depends(get_current_approver),
    service: UserService = Depends(get_user_service),
):
    """Return all users. Requires approver role."""
    return service.list_users()


@router.patch("/{user_id}/role", response_model=User)
def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: User = Depends(get_current_approver),
    service: UserService = Depends(get_user_service),
):
    """Update a user's role. Requires approver role.

    Raises 403 if attempting to change own role.
    Raises 400 if attempting to demote the last approver.
    Raises 404 if user not found.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role",
        )

    try:
        return service.update_user_role(user_id, request.role)
    except LastApproverError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote the last approver",
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
