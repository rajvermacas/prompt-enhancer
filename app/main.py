from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.dependencies import AuthRedirectException, get_settings
from app.routes import pages, workspaces, news, prompts, workflows
from app.routes.auth import router as auth_router
from app.routes.workspace_news import router as workspace_news_router
from app.routes.workspace_news import news_source_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.auth_db_path)

    # Initialize organization workspace
    from app.services.workspace_service import WorkspaceService

    workspace_service = WorkspaceService(settings.workspaces_path)
    workspace_service.init_organization_workspace()

    yield


app = FastAPI(title="Prompt Enhancer", version="0.1.0", lifespan=lifespan)


@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request, exc):
    return RedirectResponse(url="/login", status_code=303)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(pages.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(workspace_news_router, prefix="/api")
app.include_router(news_source_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
