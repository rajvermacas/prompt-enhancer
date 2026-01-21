import csv
import uuid
from pathlib import Path

from app.models.news import NewsArticle


class WorkspaceNewsService:
    def __init__(self, workspaces_path: Path, default_news_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.default_news_path = Path(default_news_path)

    def _get_uploaded_news_path(self, workspace_id: str) -> Path:
        return self.workspaces_path / workspace_id / "uploaded_news.csv"

    def add_article(
        self, workspace_id: str, headline: str, content: str, date: str
    ) -> NewsArticle:
        article_id = f"uploaded-{uuid.uuid4().hex[:8]}"
        article = NewsArticle(
            id=article_id,
            headline=headline,
            content=content,
            date=date
        )

        csv_path = self._get_uploaded_news_path(workspace_id)
        file_exists = csv_path.exists()

        with open(csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "headline", "content", "date"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "id": article.id,
                "headline": article.headline,
                "content": article.content,
                "date": article.date
            })

        return article
