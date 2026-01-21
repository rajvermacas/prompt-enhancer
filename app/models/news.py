from pydantic import BaseModel


class NewsArticle(BaseModel):
    id: str
    headline: str
    content: str
    date: str | None = None


class NewsListResponse(BaseModel):
    articles: list[NewsArticle]
    total: int
    page: int
    limit: int
