from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user_or_redirect, get_workspace_service
from app.models.auth import User
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def news_list_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    return templates.TemplateResponse(
        "news_list.html",
        {"request": request, "workspaces": workspaces, "current_user": current_user},
    )


@router.get("/prompts", response_class=HTMLResponse)
def prompts_page(
    request: Request,
    current_user: User = Depends(get_current_user_or_redirect),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces_for_user(current_user.id)
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, "workspaces": workspaces, "current_user": current_user},
    )
