from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_settings, get_workspace_service
from app.models.auth import User
from app.models.prompts import FewShotConfig, PromptConfig, SystemPromptConfig
from app.services.prompt_service import PromptService
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces/{workspace_id}/prompts", tags=["prompts"])


def get_prompt_service(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> PromptService:
    settings = get_settings()
    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace_dir = Path(settings.workspaces_path) / workspace_id
    return PromptService(workspace_dir)


@router.get("/categories", response_model=PromptConfig)
def get_categories(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    return service.get_categories()


@router.put("/categories", response_model=PromptConfig)
def save_categories(
    config: PromptConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    service.save_categories(config)
    return config


@router.get("/few-shots", response_model=FewShotConfig)
def get_few_shots(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    return service.get_few_shots()


@router.put("/few-shots", response_model=FewShotConfig)
def save_few_shots(
    config: FewShotConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    service.save_few_shots(config)
    return config


@router.get("/system-prompt", response_model=SystemPromptConfig)
def get_system_prompt(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    return service.get_system_prompt()


@router.put("/system-prompt", response_model=SystemPromptConfig)
def save_system_prompt(
    config: SystemPromptConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    service.save_system_prompt(config)
    return config
