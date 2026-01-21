# News Upload Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add workspace-scoped news upload functionality via modal with CSV bulk upload and single article form.

**Architecture:** Extend the existing workspace model with `news_source` preference. Create a new `WorkspaceNewsService` to handle uploaded news storage (CSV file per workspace) and retrieval (respecting merge/replace preference). Add API routes and modal UI for uploads.

**Tech Stack:** FastAPI, Pydantic, Jinja2/Tailwind CSS, vanilla JavaScript

---

## Task 1: Update NewsArticle Model with Date Field

**Files:**
- Modify: `app/models/news.py`
- Test: `tests/test_models_news.py`

**Step 1: Write the failing test**

Add to `tests/test_models_news.py`:

```python
def test_news_article_with_date():
    """NewsArticle accepts optional date field as string."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="test-1",
        headline="Test Headline",
        content="Test content",
        date="2026-01-15"
    )

    assert article.date == "2026-01-15"


def test_news_article_without_date():
    """NewsArticle date defaults to None."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="test-1",
        headline="Test Headline",
        content="Test content"
    )

    assert article.date is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_news.py::test_news_article_with_date tests/test_models_news.py::test_news_article_without_date -v`
Expected: FAIL with validation error

**Step 3: Write minimal implementation**

Modify `app/models/news.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_news.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/news.py tests/test_models_news.py
git commit -m "feat(models): add optional date field to NewsArticle"
```

---

## Task 2: Add NewsSource Enum

**Files:**
- Modify: `app/models/news.py`
- Test: `tests/test_models_news.py`

**Step 1: Write the failing test**

Add to `tests/test_models_news.py`:

```python
def test_news_source_enum_values():
    """NewsSource enum has merge and replace values."""
    from app.models.news import NewsSource

    assert NewsSource.MERGE.value == "merge"
    assert NewsSource.REPLACE.value == "replace"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_news.py::test_news_source_enum_values -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

Add to `app/models/news.py` (after imports):

```python
from enum import Enum

from pydantic import BaseModel


class NewsSource(str, Enum):
    MERGE = "merge"
    REPLACE = "replace"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_news.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/news.py tests/test_models_news.py
git commit -m "feat(models): add NewsSource enum for merge/replace preference"
```

---

## Task 3: Update WorkspaceMetadata with news_source Field

**Files:**
- Modify: `app/models/workspace.py`
- Test: `tests/test_models_workspace.py`

**Step 1: Write the failing test**

Add to `tests/test_models_workspace.py`:

```python
def test_workspace_metadata_news_source_default():
    """WorkspaceMetadata news_source defaults to merge."""
    from datetime import datetime
    from app.models.workspace import WorkspaceMetadata
    from app.models.news import NewsSource

    metadata = WorkspaceMetadata(
        id="ws-123",
        name="Test",
        created_at=datetime.now()
    )

    assert metadata.news_source == NewsSource.MERGE


def test_workspace_metadata_news_source_replace():
    """WorkspaceMetadata accepts replace news_source."""
    from datetime import datetime
    from app.models.workspace import WorkspaceMetadata
    from app.models.news import NewsSource

    metadata = WorkspaceMetadata(
        id="ws-123",
        name="Test",
        created_at=datetime.now(),
        news_source=NewsSource.REPLACE
    )

    assert metadata.news_source == NewsSource.REPLACE
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_workspace.py::test_workspace_metadata_news_source_default tests/test_models_workspace.py::test_workspace_metadata_news_source_replace -v`
Expected: FAIL with validation error

**Step 3: Write minimal implementation**

Modify `app/models/workspace.py`:

```python
from datetime import datetime

from pydantic import BaseModel

from app.models.news import NewsSource


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_workspace.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/workspace.py tests/test_models_workspace.py
git commit -m "feat(models): add news_source field to WorkspaceMetadata"
```

---

## Task 4: Create WorkspaceNewsService - Core Structure and get_uploaded_news_path

**Files:**
- Create: `app/services/workspace_news_service.py`
- Create: `tests/test_workspace_news_service.py`

**Step 1: Write the failing test**

Create `tests/test_workspace_news_service.py`:

```python
import pytest
from pathlib import Path


@pytest.fixture
def workspaces_dir(tmp_path):
    """Create a temporary workspaces directory with a workspace."""
    ws_dir = tmp_path / "workspaces"
    ws_dir.mkdir()
    return ws_dir


@pytest.fixture
def workspace_with_metadata(workspaces_dir):
    """Create a workspace directory with metadata."""
    import json
    from datetime import datetime

    ws_id = "ws-test123"
    ws_path = workspaces_dir / ws_id
    ws_path.mkdir()
    (ws_path / "feedback").mkdir()
    (ws_path / "evaluation_reports").mkdir()

    metadata = {
        "id": ws_id,
        "name": "Test Workspace",
        "created_at": datetime.now().isoformat(),
        "news_source": "merge"
    }
    with open(ws_path / "metadata.json", "w") as f:
        json.dump(metadata, f)

    return ws_id


def test_get_uploaded_news_path(workspaces_dir, workspace_with_metadata):
    """WorkspaceNewsService returns correct path for uploaded news CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    path = service._get_uploaded_news_path(workspace_with_metadata)

    assert path == workspaces_dir / workspace_with_metadata / "uploaded_news.csv"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_news_service.py::test_get_uploaded_news_path -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

Create `app/services/workspace_news_service.py`:

```python
from pathlib import Path


class WorkspaceNewsService:
    def __init__(self, workspaces_path: Path, default_news_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.default_news_path = Path(default_news_path)

    def _get_uploaded_news_path(self, workspace_id: str) -> Path:
        return self.workspaces_path / workspace_id / "uploaded_news.csv"
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_news_service.py tests/test_workspace_news_service.py
git commit -m "feat(services): create WorkspaceNewsService with path helper"
```

---

## Task 5: WorkspaceNewsService - add_article Method

**Files:**
- Modify: `app/services/workspace_news_service.py`
- Modify: `tests/test_workspace_news_service.py`

**Step 1: Write the failing test**

Add to `tests/test_workspace_news_service.py`:

```python
def test_add_article_creates_csv(workspaces_dir, workspace_with_metadata):
    """add_article creates uploaded_news.csv if it doesn't exist."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    article = service.add_article(
        workspace_with_metadata,
        headline="Test Headline",
        content="Test content",
        date="2026-01-15"
    )

    assert article.headline == "Test Headline"
    assert article.content == "Test content"
    assert article.date == "2026-01-15"
    assert article.id is not None
    assert (workspaces_dir / workspace_with_metadata / "uploaded_news.csv").exists()


def test_add_article_appends_to_existing_csv(workspaces_dir, workspace_with_metadata):
    """add_article appends to existing CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    service.add_article(workspace_with_metadata, "First", "Content 1", "2026-01-01")
    service.add_article(workspace_with_metadata, "Second", "Content 2", "2026-01-02")

    csv_path = workspaces_dir / workspace_with_metadata / "uploaded_news.csv"
    with open(csv_path) as f:
        lines = f.readlines()

    assert len(lines) == 3  # header + 2 articles
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_news_service.py::test_add_article_creates_csv tests/test_workspace_news_service.py::test_add_article_appends_to_existing_csv -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

Add to `app/services/workspace_news_service.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_news_service.py tests/test_workspace_news_service.py
git commit -m "feat(services): add add_article method to WorkspaceNewsService"
```

---

## Task 6: WorkspaceNewsService - upload_csv Method

**Files:**
- Modify: `app/services/workspace_news_service.py`
- Modify: `tests/test_workspace_news_service.py`

**Step 1: Write the failing test**

Add to `tests/test_workspace_news_service.py`:

```python
import io


def test_upload_csv_success(workspaces_dir, workspace_with_metadata):
    """upload_csv parses and stores articles from CSV."""
    from app.services.workspace_news_service import WorkspaceNewsService

    csv_content = "id,headline,content,date\n1,News One,Content one,2026-01-01\n2,News Two,Content two,2026-01-02"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    count = service.upload_csv(workspace_with_metadata, file)

    assert count == 2
    assert (workspaces_dir / workspace_with_metadata / "uploaded_news.csv").exists()


def test_upload_csv_missing_columns(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error when required columns are missing."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline\n1,News One"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "content" in str(exc.value).lower()
    assert "date" in str(exc.value).lower()


def test_upload_csv_empty_file(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error for empty CSV."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline,content,date\n"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "empty" in str(exc.value).lower()


def test_upload_csv_duplicate_ids(workspaces_dir, workspace_with_metadata):
    """upload_csv raises error for duplicate IDs in file."""
    from app.services.workspace_news_service import (
        WorkspaceNewsService,
        CSVValidationError
    )

    csv_content = "id,headline,content,date\n1,News One,Content,2026-01-01\n1,Duplicate,Content,2026-01-02"
    file = io.BytesIO(csv_content.encode())

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    with pytest.raises(CSVValidationError) as exc:
        service.upload_csv(workspace_with_metadata, file)

    assert "duplicate" in str(exc.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_news_service.py::test_upload_csv_success tests/test_workspace_news_service.py::test_upload_csv_missing_columns tests/test_workspace_news_service.py::test_upload_csv_empty_file tests/test_workspace_news_service.py::test_upload_csv_duplicate_ids -v`
Expected: FAIL with AttributeError or ImportError

**Step 3: Write minimal implementation**

Update `app/services/workspace_news_service.py`:

```python
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
    REQUIRED_COLUMNS = {"id", "headline", "content", "date"}

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

        missing_columns = self.REQUIRED_COLUMNS - set(reader.fieldnames)
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_news_service.py tests/test_workspace_news_service.py
git commit -m "feat(services): add upload_csv method with validation"
```

---

## Task 7: WorkspaceNewsService - get_news_source and set_news_source Methods

**Files:**
- Modify: `app/services/workspace_news_service.py`
- Modify: `tests/test_workspace_news_service.py`

**Step 1: Write the failing test**

Add to `tests/test_workspace_news_service.py`:

```python
def test_get_news_source_default(workspaces_dir, workspace_with_metadata):
    """get_news_source returns merge by default."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))
    source = service.get_news_source(workspace_with_metadata)

    assert source == NewsSource.MERGE


def test_set_news_source(workspaces_dir, workspace_with_metadata):
    """set_news_source updates workspace metadata."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, Path("/tmp/default.csv"))

    service.set_news_source(workspace_with_metadata, NewsSource.REPLACE)
    source = service.get_news_source(workspace_with_metadata)

    assert source == NewsSource.REPLACE
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_news_service.py::test_get_news_source_default tests/test_workspace_news_service.py::test_set_news_source -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

Add to `app/services/workspace_news_service.py`:

```python
import csv
import io
import json
import uuid
from pathlib import Path
from typing import BinaryIO

from app.models.news import NewsArticle, NewsSource
from app.models.workspace import WorkspaceMetadata


class CSVValidationError(Exception):
    """Raised when CSV validation fails."""
    pass


class WorkspaceNewsService:
    REQUIRED_COLUMNS = {"id", "headline", "content", "date"}

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

        missing_columns = self.REQUIRED_COLUMNS - set(reader.fieldnames)
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_news_service.py tests/test_workspace_news_service.py
git commit -m "feat(services): add get/set news_source methods"
```

---

## Task 8: WorkspaceNewsService - get_news Method

**Files:**
- Modify: `app/services/workspace_news_service.py`
- Modify: `tests/test_workspace_news_service.py`

**Step 1: Write the failing test**

Add to `tests/test_workspace_news_service.py`:

```python
@pytest.fixture
def default_news_csv(tmp_path):
    """Create default news CSV."""
    csv_path = tmp_path / "default_news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        for i in range(5):
            writer.writerow({
                "id": f"default-{i}",
                "headline": f"Default Headline {i}",
                "content": f"Default content {i}"
            })
    return csv_path


def test_get_news_merge_mode(workspaces_dir, workspace_with_metadata, default_news_csv):
    """get_news returns merged default + uploaded news in merge mode."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, default_news_csv)
    service.add_article(workspace_with_metadata, "Uploaded", "Content", "2026-01-01")

    response = service.get_news(workspace_with_metadata, page=1, limit=10)

    assert response.total == 6  # 5 default + 1 uploaded
    headlines = [a.headline for a in response.articles]
    assert "Uploaded" in headlines
    assert "Default Headline 0" in headlines


def test_get_news_replace_mode_with_uploads(workspaces_dir, workspace_with_metadata, default_news_csv):
    """get_news returns only uploaded news in replace mode when uploads exist."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, default_news_csv)
    service.add_article(workspace_with_metadata, "Uploaded", "Content", "2026-01-01")
    service.set_news_source(workspace_with_metadata, NewsSource.REPLACE)

    response = service.get_news(workspace_with_metadata, page=1, limit=10)

    assert response.total == 1
    assert response.articles[0].headline == "Uploaded"


def test_get_news_replace_mode_fallback(workspaces_dir, workspace_with_metadata, default_news_csv):
    """get_news falls back to default news in replace mode when no uploads."""
    from app.services.workspace_news_service import WorkspaceNewsService
    from app.models.news import NewsSource

    service = WorkspaceNewsService(workspaces_dir, default_news_csv)
    service.set_news_source(workspace_with_metadata, NewsSource.REPLACE)

    response = service.get_news(workspace_with_metadata, page=1, limit=10)

    assert response.total == 5  # Falls back to default
    assert response.articles[0].headline == "Default Headline 0"


def test_get_news_pagination(workspaces_dir, workspace_with_metadata, default_news_csv):
    """get_news respects pagination parameters."""
    from app.services.workspace_news_service import WorkspaceNewsService

    service = WorkspaceNewsService(workspaces_dir, default_news_csv)

    response = service.get_news(workspace_with_metadata, page=2, limit=2)

    assert len(response.articles) == 2
    assert response.page == 2
    assert response.limit == 2
    assert response.total == 5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_news_service.py::test_get_news_merge_mode tests/test_workspace_news_service.py::test_get_news_replace_mode_with_uploads tests/test_workspace_news_service.py::test_get_news_replace_mode_fallback tests/test_workspace_news_service.py::test_get_news_pagination -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

Add the `get_news` method and helper methods to `app/services/workspace_news_service.py`. Update the full file:

```python
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


class WorkspaceNewsService:
    REQUIRED_COLUMNS = {"id", "headline", "content", "date"}

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

    def get_news_source(self, workspace_id: str) -> NewsSource:
        metadata = self._load_metadata(workspace_id)
        return metadata.news_source

    def set_news_source(self, workspace_id: str, source: NewsSource) -> None:
        metadata = self._load_metadata(workspace_id)
        metadata.news_source = source
        self._save_metadata(workspace_id, metadata)

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

        missing_columns = self.REQUIRED_COLUMNS - set(reader.fieldnames)
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_news_service.py tests/test_workspace_news_service.py
git commit -m "feat(services): add get_news method with merge/replace logic"
```

---

## Task 9: Add Dependency Injection for WorkspaceNewsService

**Files:**
- Modify: `app/dependencies.py`

**Step 1: Modify dependencies.py**

No test needed - simple wiring. Add to `app/dependencies.py`:

```python
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
```

**Step 2: Run all tests to verify nothing broke**

Run: `uv run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
git add app/dependencies.py
git commit -m "feat(deps): add WorkspaceNewsService dependency injection"
```

---

## Task 10: Create API Routes for News Upload

**Files:**
- Create: `app/routes/workspace_news.py`
- Create: `tests/test_routes_workspace_news.py`

**Step 1: Write the failing tests**

Create `tests/test_routes_workspace_news.py`:

```python
import csv
import io
import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with temporary data directories."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))

    # Create default news CSV
    with open(tmp_path / "news.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        writer.writerow({"id": "default-1", "headline": "Default News", "content": "Content"})

    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.dependencies import get_settings
    get_settings.cache_clear()

    from app.main import app
    return TestClient(app)


@pytest.fixture
def workspace_id(client):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json={"name": "Test WS"})
    return response.json()["id"]


def test_add_single_article(client, workspace_id):
    """POST /api/workspaces/{id}/news adds a single article."""
    response = client.post(
        f"/api/workspaces/{workspace_id}/news",
        json={"headline": "New Article", "content": "Article content", "date": "2026-01-15"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["headline"] == "New Article"
    assert data["content"] == "Article content"
    assert data["date"] == "2026-01-15"
    assert "id" in data


def test_upload_csv(client, workspace_id):
    """POST /api/workspaces/{id}/news/upload-csv uploads CSV file."""
    csv_content = "id,headline,content,date\n1,CSV News,CSV Content,2026-01-01"
    files = {"file": ("news.csv", io.BytesIO(csv_content.encode()), "text/csv")}

    response = client.post(
        f"/api/workspaces/{workspace_id}/news/upload-csv",
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_get_workspace_news(client, workspace_id):
    """GET /api/workspaces/{id}/news returns news for workspace."""
    response = client.get(f"/api/workspaces/{workspace_id}/news?page=1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert data["total"] == 1  # Default news


def test_set_news_source(client, workspace_id):
    """PUT /api/workspaces/{id}/news-source updates preference."""
    response = client.put(
        f"/api/workspaces/{workspace_id}/news-source",
        json={"news_source": "replace"}
    )

    assert response.status_code == 200
    assert response.json()["news_source"] == "replace"


def test_get_news_source(client, workspace_id):
    """GET /api/workspaces/{id}/news-source returns current preference."""
    response = client.get(f"/api/workspaces/{workspace_id}/news-source")

    assert response.status_code == 200
    assert response.json()["news_source"] == "merge"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_routes_workspace_news.py -v`
Expected: FAIL with 404 errors (routes don't exist)

**Step 3: Write minimal implementation**

Create `app/routes/workspace_news.py`:

```python
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
```

**Step 4: Register routes in main.py**

Update `app/main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import pages, workspaces, news, prompts, workflows
from app.routes.workspace_news import router as workspace_news_router
from app.routes.workspace_news import news_source_router

app = FastAPI(title="Prompt Enhancer", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(workspace_news_router, prefix="/api")
app.include_router(news_source_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_routes_workspace_news.py -v`
Expected: PASS

**Step 6: Run all tests**

Run: `uv run pytest -v`
Expected: PASS

**Step 7: Commit**

```bash
git add app/routes/workspace_news.py app/main.py tests/test_routes_workspace_news.py
git commit -m "feat(routes): add workspace news upload API endpoints"
```

---

## Task 11: Add Upload News Button to UI

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add upload button and modal HTML**

In `app/templates/news_list.html`, update the header section (after line 8):

```html
{% extends "base.html" %}

{% block title %}News - Prompt Enhancer{% endblock %}

{% block content %}
<div class="mb-8 flex justify-between items-center">
    <h1 class="text-2xl font-semibold text-gray-900">News Articles</h1>
    <button id="upload-news-btn"
            onclick="openUploadModal()"
            class="hidden bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-500 transition-all duration-200">
        Upload News
    </button>
</div>

<!-- Upload News Modal -->
<div id="upload-modal" class="fixed inset-0 bg-black/50 z-50 hidden items-center justify-center">
    <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center p-6 border-b border-gray-200">
            <h2 class="text-xl font-semibold text-gray-900">Upload News</h2>
            <button onclick="closeUploadModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>

        <div class="p-6">
            <!-- Tabs -->
            <div class="flex border-b border-gray-200 mb-6">
                <button id="tab-csv" onclick="switchTab('csv')"
                        class="px-4 py-2 font-medium text-red-600 border-b-2 border-red-600">
                    CSV Upload
                </button>
                <button id="tab-single" onclick="switchTab('single')"
                        class="px-4 py-2 font-medium text-gray-500 hover:text-gray-700">
                    Single Article
                </button>
            </div>

            <!-- CSV Upload Tab -->
            <div id="content-csv" class="tab-content">
                <p class="text-sm text-gray-600 mb-4">
                    Upload a CSV file with columns: <code class="bg-gray-100 px-1 rounded">id</code>,
                    <code class="bg-gray-100 px-1 rounded">headline</code>,
                    <code class="bg-gray-100 px-1 rounded">content</code>,
                    <code class="bg-gray-100 px-1 rounded">date</code>
                </p>
                <div id="csv-dropzone"
                     class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-red-400 transition-colors cursor-pointer"
                     onclick="document.getElementById('csv-file-input').click()">
                    <svg class="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                    </svg>
                    <p class="text-gray-600" id="csv-filename">Drop CSV file here or click to browse</p>
                    <input type="file" id="csv-file-input" accept=".csv" class="hidden" onchange="handleFileSelect(this)">
                </div>
            </div>

            <!-- Single Article Tab -->
            <div id="content-single" class="tab-content hidden">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Headline</label>
                        <input type="text" id="article-headline"
                               class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none"
                               placeholder="Enter headline">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
                        <input type="text" id="article-date"
                               class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none"
                               placeholder="e.g., 2026-01-15, Jan 15 2026">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Content</label>
                        <textarea id="article-content" rows="5"
                                  class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none resize-none"
                                  placeholder="Enter article content"></textarea>
                    </div>
                </div>
            </div>

            <!-- News Source Toggle -->
            <div class="mt-6 pt-6 border-t border-gray-200">
                <label class="block text-sm font-medium text-gray-700 mb-3">News Source</label>
                <div class="flex gap-4">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="news-source" value="merge" checked
                               class="text-red-600 focus:ring-red-600"
                               onchange="updateNewsSource(this.value)">
                        <span class="text-sm text-gray-700">Merge</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="news-source" value="replace"
                               class="text-red-600 focus:ring-red-600"
                               onchange="updateNewsSource(this.value)">
                        <span class="text-sm text-gray-700">Replace</span>
                    </label>
                </div>
                <p class="text-xs text-gray-500 mt-2">
                    Merge: Show uploaded + default news. Replace: Show only uploaded news.
                </p>
            </div>
        </div>

        <div class="flex justify-end gap-3 p-6 border-t border-gray-200">
            <button onclick="closeUploadModal()"
                    class="px-4 py-2 text-gray-700 font-medium hover:bg-gray-100 rounded-lg transition-colors">
                Cancel
            </button>
            <button id="upload-submit-btn" onclick="submitUpload()"
                    class="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-500 transition-colors">
                Upload
            </button>
        </div>
    </div>
</div>

<div id="news-list" class="space-y-5">
    <div class="text-center py-8 text-gray-500">Loading news...</div>
</div>
{% endblock %}
```

**Step 2: Commit HTML changes**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): add upload news button and modal HTML structure"
```

---

## Task 12: Add JavaScript for Upload Modal Functionality

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add JavaScript functions**

Add the following JavaScript functions to the `{% block scripts %}` section in `app/templates/news_list.html`, before the existing script content:

```javascript
    // Upload modal state
    let selectedFile = null;
    let currentTab = localStorage.getItem('uploadTab') || 'csv';

    function openUploadModal() {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }

        document.getElementById('upload-modal').classList.remove('hidden');
        document.getElementById('upload-modal').classList.add('flex');

        // Load current news source preference
        fetch(`/api/workspaces/${wsId}/news-source`)
            .then(r => r.json())
            .then(data => {
                const radios = document.querySelectorAll('input[name="news-source"]');
                radios.forEach(r => r.checked = r.value === data.news_source);
            });

        // Restore last tab
        switchTab(currentTab);
    }

    function closeUploadModal() {
        document.getElementById('upload-modal').classList.add('hidden');
        document.getElementById('upload-modal').classList.remove('flex');
        resetUploadForm();
    }

    function resetUploadForm() {
        selectedFile = null;
        document.getElementById('csv-file-input').value = '';
        document.getElementById('csv-filename').textContent = 'Drop CSV file here or click to browse';
        document.getElementById('article-headline').value = '';
        document.getElementById('article-date').value = '';
        document.getElementById('article-content').value = '';
    }

    function switchTab(tab) {
        currentTab = tab;
        localStorage.setItem('uploadTab', tab);

        // Update tab buttons
        document.getElementById('tab-csv').classList.toggle('text-red-600', tab === 'csv');
        document.getElementById('tab-csv').classList.toggle('border-b-2', tab === 'csv');
        document.getElementById('tab-csv').classList.toggle('border-red-600', tab === 'csv');
        document.getElementById('tab-csv').classList.toggle('text-gray-500', tab !== 'csv');

        document.getElementById('tab-single').classList.toggle('text-red-600', tab === 'single');
        document.getElementById('tab-single').classList.toggle('border-b-2', tab === 'single');
        document.getElementById('tab-single').classList.toggle('border-red-600', tab === 'single');
        document.getElementById('tab-single').classList.toggle('text-gray-500', tab !== 'single');

        // Update content
        document.getElementById('content-csv').classList.toggle('hidden', tab !== 'csv');
        document.getElementById('content-single').classList.toggle('hidden', tab !== 'single');

        // Update button text
        document.getElementById('upload-submit-btn').textContent = tab === 'csv' ? 'Upload' : 'Save';
    }

    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            document.getElementById('csv-filename').textContent = selectedFile.name;
        }
    }

    function updateNewsSource(value) {
        const wsId = getWorkspaceId();
        fetch(`/api/workspaces/${wsId}/news-source`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({news_source: value})
        });
    }

    function submitUpload() {
        if (currentTab === 'csv') {
            submitCSVUpload();
        } else {
            submitSingleArticle();
        }
    }

    function submitCSVUpload() {
        if (!selectedFile) {
            alert('Please select a CSV file');
            return;
        }

        const wsId = getWorkspaceId();
        const formData = new FormData();
        formData.append('file', selectedFile);

        const btn = document.getElementById('upload-submit-btn');
        btn.disabled = true;
        btn.textContent = 'Uploading...';

        fetch(`/api/workspaces/${wsId}/news/upload-csv`, {
            method: 'POST',
            body: formData
        })
        .then(r => {
            if (!r.ok) return r.json().then(e => Promise.reject(e));
            return r.json();
        })
        .then(data => {
            alert(`Successfully uploaded ${data.count} articles`);
            closeUploadModal();
            loadNews();
        })
        .catch(err => {
            alert('Upload failed: ' + (err.detail || err.message || 'Unknown error'));
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = 'Upload';
        });
    }

    function submitSingleArticle() {
        const headline = document.getElementById('article-headline').value.trim();
        const date = document.getElementById('article-date').value.trim();
        const content = document.getElementById('article-content').value.trim();

        if (!headline || !date || !content) {
            alert('All fields are required');
            return;
        }

        const wsId = getWorkspaceId();
        const btn = document.getElementById('upload-submit-btn');
        btn.disabled = true;
        btn.textContent = 'Saving...';

        fetch(`/api/workspaces/${wsId}/news`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({headline, content, date})
        })
        .then(r => {
            if (!r.ok) return r.json().then(e => Promise.reject(e));
            return r.json();
        })
        .then(data => {
            alert('Article added successfully');
            closeUploadModal();
            loadNews();
        })
        .catch(err => {
            alert('Failed to add article: ' + (err.detail || err.message || 'Unknown error'));
        })
        .finally(() => {
            btn.disabled = false;
            btn.textContent = 'Save';
        });
    }

    // Show/hide upload button based on workspace selection
    function updateUploadButtonVisibility() {
        const wsId = getWorkspaceId();
        const btn = document.getElementById('upload-news-btn');
        if (wsId) {
            btn.classList.remove('hidden');
        } else {
            btn.classList.add('hidden');
        }
    }

    // Override workspace selector change to update button visibility
    document.getElementById('workspace-selector').addEventListener('change', function() {
        localStorage.setItem('selectedWorkspaceId', this.value);
        updateUploadButtonVisibility();
        loadNews();
    });
```

**Step 2: Update loadNews function to use workspace-scoped endpoint when workspace is selected**

Update the `loadNews` function:

```javascript
    function loadNews() {
        const wsId = getWorkspaceId();
        let url = '/api/news?page=1&limit=20';

        if (wsId) {
            url = `/api/workspaces/${wsId}/news?page=1&limit=20`;
        }

        fetch(url)
            .then(r => r.json())
            .then(data => {
                renderNewsList(data);
            });
    }
```

**Step 3: Update DOMContentLoaded to call updateUploadButtonVisibility**

Update the DOMContentLoaded handler:

```javascript
    // Load news on page load
    document.addEventListener('DOMContentLoaded', function() {
        updateUploadButtonVisibility();
        loadNews();
    });
```

**Step 4: Run the app and test manually**

Run: `uv run uvicorn app.main:app --reload`
Test: Open browser, select workspace, verify upload button appears, test modal functionality.

**Step 5: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): add JavaScript for upload modal functionality"
```

---

## Task 13: Add Drag and Drop Support for CSV Upload

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add drag and drop event handlers**

Add to the JavaScript section:

```javascript
    // Drag and drop support
    const dropzone = document.getElementById('csv-dropzone');

    if (dropzone) {
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('border-red-400', 'bg-red-50');
        });

        dropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('border-red-400', 'bg-red-50');
        });

        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('border-red-400', 'bg-red-50');

            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                const file = e.dataTransfer.files[0];
                if (file.name.endsWith('.csv')) {
                    selectedFile = file;
                    document.getElementById('csv-filename').textContent = file.name;
                } else {
                    alert('Please drop a CSV file');
                }
            }
        });
    }
```

**Step 2: Test manually**

Run: `uv run uvicorn app.main:app --reload`
Test: Drag a CSV file onto the dropzone.

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): add drag and drop support for CSV upload"
```

---

## Task 14: Run All Tests and Final Verification

**Step 1: Run all tests**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Run linting (if configured)**

Run: `uv run ruff check .`
Expected: No errors

**Step 3: Manual testing checklist**

Start the app: `uv run uvicorn app.main:app --reload`

- [ ] Create a new workspace
- [ ] Verify "Upload News" button appears when workspace is selected
- [ ] Open upload modal
- [ ] Test CSV upload tab - upload a valid CSV file
- [ ] Verify uploaded articles appear in news list
- [ ] Test Single Article tab - add an article manually
- [ ] Verify the new article appears in news list
- [ ] Test News Source toggle (Merge vs Replace)
- [ ] Verify Merge shows both uploaded and default news
- [ ] Verify Replace shows only uploaded news (or falls back to default if none)
- [ ] Test drag and drop for CSV upload
- [ ] Verify modal closes after successful upload
- [ ] Verify error messages for invalid CSV

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete news upload feature implementation"
```

---

## Summary

This implementation plan covers:

1. **Model Updates** (Tasks 1-3): Add `date` field to `NewsArticle`, create `NewsSource` enum, update `WorkspaceMetadata`

2. **Service Layer** (Tasks 4-8): Create `WorkspaceNewsService` with methods for:
   - Adding single articles
   - Uploading CSV files with validation
   - Getting/setting news source preference
   - Retrieving news with merge/replace logic

3. **API Layer** (Tasks 9-10): Add dependency injection and create REST endpoints

4. **UI Layer** (Tasks 11-13): Add upload button, modal with tabs, and drag-drop support

5. **Final Verification** (Task 14): Run tests and manual testing
