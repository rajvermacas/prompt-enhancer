from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_workspace_service
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def news_list_page(
    request: Request,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces()
    return templates.TemplateResponse(
        "news_list.html",
        {"request": request, "workspaces": workspaces},
    )


@router.get("/prompts", response_class=HTMLResponse)
def prompts_page(
    request: Request,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces()
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, "workspaces": workspaces},
    )
