from functools import lru_cache
from pathlib import Path

from app.config import Settings
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
