from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user, get_news_service
from app.models.auth import User
from app.models.news import NewsArticle, NewsListResponse
from app.services.news_service import ArticleNotFoundError, NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    return service.get_news(page=page, limit=limit)


@router.get("/{article_id}", response_model=NewsArticle)
def get_article(
    article_id: str,
    current_user: User = Depends(get_current_user),
    service: NewsService = Depends(get_news_service),
):
    try:
        return service.get_article(article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")
