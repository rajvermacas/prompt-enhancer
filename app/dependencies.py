from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, Request

from app.config import Settings
from app.db import SessionExpiredError, SessionNotFoundError
from app.services.auth_service import AuthService
from app.services.workspace_service import WorkspaceService
from app.services.news_service import NewsService
from app.services.workspace_news_service import WorkspaceNewsService
from app.agents.llm_provider import get_llm


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_workspace_service() -> WorkspaceService:
    settings = get_settings()
    return WorkspaceService(Path(settings.workspaces_path))


def get_news_service() -> NewsService:
    settings = get_settings()
    return NewsService(Path(settings.news_csv_path))


def get_workspace_news_service() -> WorkspaceNewsService:
    settings = get_settings()
    return WorkspaceNewsService(
        Path(settings.workspaces_path),
        Path(settings.news_csv_path)
    )


def get_system_prompt() -> str:
    settings = get_settings()
    with open(settings.system_prompt_path) as f:
        return f.read()


class AuthRedirectException(Exception):
    """Raised to trigger redirect to login page."""
    pass


def get_auth_service() -> AuthService:
    settings = get_settings()
    return AuthService(settings.auth_db_path)


def get_current_user(request: Request):
    """For API routes. Returns User or raises HTTPException(401)."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_service = get_auth_service()
    try:
        return auth_service.validate_session(session_id)
    except (SessionNotFoundError, SessionExpiredError):
        raise HTTPException(
            status_code=401, detail="Session invalid or expired"
        )


def get_current_user_or_redirect(request: Request):
    """For page routes. Returns User or raises AuthRedirectException."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise AuthRedirectException()

    auth_service = get_auth_service()
    try:
        return auth_service.validate_session(session_id)
    except (SessionNotFoundError, SessionExpiredError):
        raise AuthRedirectException()
