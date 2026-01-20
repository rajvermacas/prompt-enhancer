from pydantic import BaseModel


class NewsArticle(BaseModel):
    id: str
    headline: str
    content: str


class NewsListResponse(BaseModel):
    articles: list[NewsArticle]
    total: int
    page: int
    limit: int
