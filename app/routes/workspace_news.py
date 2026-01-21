from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.dependencies import get_workspace_news_service
from app.models.news import NewsArticle, NewsListResponse, NewsSource
from app.services.workspace_news_service import (
    CSVValidationError,
    WorkspaceNewsService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/news", tags=["workspace-news"])


class AddArticleRequest(BaseModel):
    headline: str
    content: str
    date: str


class UploadCSVResponse(BaseModel):
    count: int
    message: str


class NewsSourceRequest(BaseModel):
    news_source: NewsSource


class NewsSourceResponse(BaseModel):
    news_source: NewsSource


@router.post("", status_code=status.HTTP_201_CREATED, response_model=NewsArticle)
def add_article(
    workspace_id: str,
    request: AddArticleRequest,
    service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    return service.add_article(
        workspace_id,
        request.headline,
        request.content,
        request.date
    )


@router.post("/upload-csv", response_model=UploadCSVResponse)
async def upload_csv(
    workspace_id: str,
    file: UploadFile = File(...),
    service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    try:
        count = service.upload_csv(workspace_id, file.file)
        return UploadCSVResponse(count=count, message=f"{count} articles uploaded")
    except CSVValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=NewsListResponse)
def get_news(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    return service.get_news(workspace_id, page, limit)


# News source endpoints - separate prefix
news_source_router = APIRouter(
    prefix="/workspaces/{workspace_id}/news-source",
    tags=["workspace-news"]
)


@news_source_router.get("", response_model=NewsSourceResponse)
def get_news_source(
    workspace_id: str,
    service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    return NewsSourceResponse(news_source=service.get_news_source(workspace_id))


@news_source_router.put("", response_model=NewsSourceResponse)
def set_news_source(
    workspace_id: str,
    request: NewsSourceRequest,
    service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    service.set_news_source(workspace_id, request.news_source)
    return NewsSourceResponse(news_source=request.news_source)
