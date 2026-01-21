import csv
import io
import json
import uuid
from pathlib import Path
from typing import BinaryIO

from app.models.news import NewsArticle, NewsListResponse, NewsSource
from app.models.workspace import WorkspaceMetadata


class CSVValidationError(Exception):
    """Raised when CSV validation fails."""
    pass


class ArticleNotFoundError(Exception):
    """Raised when an article is not found in the workspace."""

    def __init__(self, article_id: str):
        self.article_id = article_id
        super().__init__(f"Article not found: {article_id}")


class WorkspaceNewsService:
    def __init__(self, workspaces_path: Path, default_news_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.default_news_path = Path(default_news_path)

    def _get_uploaded_news_path(self, workspace_id: str) -> Path:
        return self.workspaces_path / workspace_id / "uploaded_news.csv"

    def _get_metadata_path(self, workspace_id: str) -> Path:
        return self.workspaces_path / workspace_id / "metadata.json"

    def _load_metadata(self, workspace_id: str) -> WorkspaceMetadata:
        with open(self._get_metadata_path(workspace_id)) as f:
            return WorkspaceMetadata.model_validate(json.load(f))

    def _save_metadata(self, workspace_id: str, metadata: WorkspaceMetadata) -> None:
        with open(self._get_metadata_path(workspace_id), "w") as f:
            json.dump(metadata.model_dump(mode="json"), f, indent=2)

    def get_news_source(self, workspace_id: str) -> NewsSource:
        metadata = self._load_metadata(workspace_id)
        return metadata.news_source

    def set_news_source(self, workspace_id: str, source: NewsSource) -> None:
        metadata = self._load_metadata(workspace_id)
        metadata.news_source = source
        self._save_metadata(workspace_id, metadata)

    def _load_default_news(self) -> list[NewsArticle]:
        articles = []
        with open(self.default_news_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                articles.append(NewsArticle(
                    id=row["id"],
                    headline=row["headline"],
                    content=row["content"],
                    date=row.get("date")
                ))
        return articles

    def _load_uploaded_news(self, workspace_id: str) -> list[NewsArticle]:
        csv_path = self._get_uploaded_news_path(workspace_id)
        if not csv_path.exists():
            return []

        articles = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                articles.append(NewsArticle(
                    id=row["id"],
                    headline=row["headline"],
                    content=row["content"],
                    date=row.get("date")
                ))
        return articles

    def get_news(self, workspace_id: str, page: int, limit: int) -> NewsListResponse:
        news_source = self.get_news_source(workspace_id)
        uploaded = self._load_uploaded_news(workspace_id)

        if news_source == NewsSource.REPLACE and uploaded:
            articles = uploaded
        elif news_source == NewsSource.REPLACE and not uploaded:
            articles = self._load_default_news()
        else:  # MERGE
            articles = uploaded + self._load_default_news()

        total = len(articles)
        start = (page - 1) * limit
        end = start + limit
        page_articles = articles[start:end]

        return NewsListResponse(
            articles=page_articles,
            total=total,
            page=page,
            limit=limit
        )

    def get_article(self, workspace_id: str, article_id: str) -> NewsArticle:
        news_source = self.get_news_source(workspace_id)
        uploaded = self._load_uploaded_news(workspace_id)

        if news_source == NewsSource.REPLACE and uploaded:
            articles = uploaded
        elif news_source == NewsSource.REPLACE and not uploaded:
            articles = self._load_default_news()
        else:  # MERGE
            articles = uploaded + self._load_default_news()

        for article in articles:
            if article.id == article_id:
                return article

        raise ArticleNotFoundError(article_id)

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

    def upload_csv(self, workspace_id: str, file: BinaryIO) -> int:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        if reader.fieldnames is None:
            raise CSVValidationError("CSV file is empty or has no header")

        required_columns = {"id", "headline", "content", "date"}
        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            raise CSVValidationError(
                f"CSV must have columns: {', '.join(sorted(missing_columns))}"
            )

        rows = list(reader)
        if not rows:
            raise CSVValidationError("CSV file is empty - no data rows")

        seen_ids: set[str] = set()
        for row in rows:
            article_id = row["id"]
            if article_id in seen_ids:
                raise CSVValidationError(f"Duplicate id '{article_id}' found in CSV")
            seen_ids.add(article_id)

        csv_path = self._get_uploaded_news_path(workspace_id)
        file_exists = csv_path.exists()

        with open(csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "headline", "content", "date"])
            if not file_exists:
                writer.writeheader()
            for row in rows:
                writer.writerow({
                    "id": row["id"],
                    "headline": row["headline"],
                    "content": row["content"],
                    "date": row["date"]
                })

        return len(rows)
