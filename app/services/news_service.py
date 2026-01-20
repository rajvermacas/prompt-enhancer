import csv
from pathlib import Path

from app.models.news import NewsArticle, NewsListResponse


class ArticleNotFoundError(Exception):
    """Raised when an article is not found."""

    def __init__(self, article_id: str):
        self.article_id = article_id
        super().__init__(f"Article not found: {article_id}")


class NewsService:
    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)
        self._articles: list[NewsArticle] | None = None

    def _load_articles(self) -> list[NewsArticle]:
        if self._articles is None:
            self._articles = []
            with open(self.csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._articles.append(NewsArticle(
                        id=row["id"],
                        headline=row["headline"],
                        content=row["content"],
                    ))
        return self._articles

    def get_news(self, page: int, limit: int) -> NewsListResponse:
        articles = self._load_articles()
        total = len(articles)

        start = (page - 1) * limit
        end = start + limit
        page_articles = articles[start:end]

        return NewsListResponse(
            articles=page_articles,
            total=total,
            page=page,
            limit=limit,
        )

    def get_article(self, article_id: str) -> NewsArticle:
        articles = self._load_articles()
        for article in articles:
            if article.id == article_id:
                return article
        raise ArticleNotFoundError(article_id)
