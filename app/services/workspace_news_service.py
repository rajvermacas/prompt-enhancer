import csv
import io
import uuid
from pathlib import Path
from typing import BinaryIO

from app.models.news import NewsArticle


class CSVValidationError(Exception):
    """Raised when CSV validation fails."""
    pass


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
