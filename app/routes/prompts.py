from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies import (
    get_change_request_service,
    get_current_user,
    get_settings,
    get_workspace_service,
)
from app.models.auth import User, UserRole
from app.models.change_request import PromptType
from app.models.prompts import FewShotConfig, PromptConfig, SystemPromptConfig
from app.services.change_request_service import (
    ChangeRequestService,
    DuplicatePendingRequestError,
)
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


@router.put("/categories")
def save_categories(
    workspace_id: str,
    config: PromptConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.CATEGORY_DEFINITIONS,
                proposed_content=config.model_dump(),
            )
            return JSONResponse(
                status_code=202, content=change_request.model_dump(mode="json")
            )
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    service.save_categories(config)
    return config


@router.get("/few-shots", response_model=FewShotConfig)
def get_few_shots(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    return service.get_few_shots()


@router.put("/few-shots")
def save_few_shots(
    workspace_id: str,
    config: FewShotConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.FEW_SHOTS,
                proposed_content=config.model_dump(),
            )
            return JSONResponse(
                status_code=202, content=change_request.model_dump(mode="json")
            )
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    service.save_few_shots(config)
    return config


@router.get("/system-prompt", response_model=SystemPromptConfig)
def get_system_prompt(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
):
    return service.get_system_prompt()


@router.put("/system-prompt")
def save_system_prompt(
    workspace_id: str,
    config: SystemPromptConfig,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service),
    change_request_service: ChangeRequestService = Depends(get_change_request_service),
):
    if workspace_id == "organization" and current_user.role != UserRole.APPROVER:
        try:
            change_request = change_request_service.create_change_request(
                user_id=current_user.id,
                prompt_type=PromptType.SYSTEM_PROMPT,
                proposed_content=config.model_dump(),
            )
            return JSONResponse(
                status_code=202, content=change_request.model_dump(mode="json")
            )
        except DuplicatePendingRequestError as e:
            raise HTTPException(status_code=409, detail=str(e))

    service.save_system_prompt(config)
    return config
