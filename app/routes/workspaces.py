from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_user, get_settings, get_workspace_service
from app.models.auth import User
from app.models.workspace import WorkspaceMetadata
from app.services.prompt_service import PromptService
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkspaceMetadata)
def create_workspace(
    request: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.create_workspace(request.name, current_user.id)


@router.get("", response_model=list[WorkspaceMetadata])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.list_workspaces_for_user(current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceMetadata)
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        service.delete_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.post("/{workspace_id}/copy-from-organization")
def copy_from_organization(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    """Copy prompts from organization workspace to user workspace."""
    # Cannot copy to organization workspace
    if workspace_id == "organization":
        raise HTTPException(
            status_code=400, detail="Cannot copy to organization workspace"
        )

    # Verify workspace exists and user owns it
    try:
        workspace = workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cannot copy to workspace you don't own"
        )

    # Get workspace paths
    settings = get_settings()
    workspaces_path = Path(settings.workspaces_path)
    org_workspace_dir = workspaces_path / "organization"
    user_workspace_dir = workspaces_path / workspace_id

    # Create prompt services for both workspaces
    org_prompt_service = PromptService(org_workspace_dir)
    user_prompt_service = PromptService(user_workspace_dir)

    # Get org prompts
    org_categories = org_prompt_service.get_categories()
    org_few_shots = org_prompt_service.get_few_shots()
    org_system_prompt = org_prompt_service.get_system_prompt()

    # Save to user workspace
    user_prompt_service.save_categories(org_categories)
    user_prompt_service.save_few_shots(org_few_shots)
    user_prompt_service.save_system_prompt(org_system_prompt)

    return {"success": True}
