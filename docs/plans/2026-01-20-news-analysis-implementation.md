# News Analysis Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a prompt optimization workbench for compliance teams to classify news and iteratively refine prompts through feedback loops.

**Architecture:** FastAPI backend serving HTMX+Tailwind UI, with three LangChain agents (Analysis, Evaluation, Improvement). File-based persistence for workspaces, prompts, and feedback. Configurable LLM provider (OpenRouter/Azure/Gemini).

**Tech Stack:** Python 3.11+, FastAPI, LangChain, HTMX, Tailwind CSS, Pydantic, uv

---

## Phase 1: Project Setup

### Task 1: Initialize Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.python-version`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "prompt-enhancer"
version = "0.1.0"
description = "News analysis agent with prompt optimization"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-google-genai>=2.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 2: Create .env.example**

```
# LLM Provider: "openrouter" | "azure" | "gemini"
LLM_PROVIDER=openrouter

# OpenRouter
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Azure OpenAI
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

# Gemini
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-1.5-pro

# Data paths
NEWS_CSV_PATH=./data/news.csv
WORKSPACES_PATH=./data/workspaces
SYSTEM_PROMPT_PATH=./prompts/system_prompt.txt
```

**Step 3: Create .python-version**

```
3.11
```

**Step 4: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed successfully

**Step 5: Commit**

```bash
git add pyproject.toml .env.example .python-version
git commit -m "feat: initialize python project with uv"
```

---

### Task 2: Create Directory Structure

**Files:**
- Create: `app/__init__.py`
- Create: `app/routes/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/agents/__init__.py`
- Create: `app/models/__init__.py`
- Create: `app/templates/.gitkeep`
- Create: `static/css/.gitkeep`
- Create: `data/.gitkeep`
- Create: `prompts/system_prompt.txt`
- Create: `tests/__init__.py`

**Step 1: Create all directories and init files**

```bash
mkdir -p app/routes app/services app/agents app/models app/templates
mkdir -p static/css data tests
touch app/__init__.py app/routes/__init__.py app/services/__init__.py
touch app/agents/__init__.py app/models/__init__.py
touch app/templates/.gitkeep static/css/.gitkeep data/.gitkeep
touch tests/__init__.py
```

**Step 2: Create initial system prompt**

Create `prompts/system_prompt.txt`:
```
You are a news analysis agent specializing in identifying price-sensitive information for compliance purposes.

Your task is to classify news articles into the appropriate category based on the category definitions provided.

## Output Format

Always respond with:
1. The category name
2. A reasoning table with 3 columns:
   - Column 1: Verbatim excerpt from the category definition that applies
   - Column 2: Verbatim excerpt from the news article that matches
   - Column 3: Your reasoning explaining why this excerpt matches the definition

3. A confidence score between 0 and 1

## Guidelines
- Be precise and cite verbatim text
- Consider all categories before deciding
- If uncertain between categories, choose the more conservative (price-sensitive) option
- Explain why the article does NOT fit other categories in your reasoning
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: create project directory structure"
```

---

### Task 3: Configuration Module

**Files:**
- Create: `app/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

Create `tests/test_config.py`:
```python
import pytest
from pydantic import ValidationError


def test_config_requires_llm_provider(monkeypatch):
    """Config must have LLM_PROVIDER set."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.config import Settings
    with pytest.raises(ValidationError):
        Settings()


def test_config_loads_openrouter_settings(monkeypatch):
    """Config loads OpenRouter settings when provider is openrouter."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.config import Settings
    settings = Settings()

    assert settings.llm_provider == "openrouter"
    assert settings.openrouter_api_key == "test-key"
    assert settings.openrouter_model == "anthropic/claude-3.5-sonnet"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.config'"

**Step 3: Write minimal implementation**

Create `app/config.py`:
```python
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # LLM Provider
    llm_provider: Literal["openrouter", "azure", "gemini"]

    # OpenRouter
    openrouter_api_key: str | None = None
    openrouter_model: str = "anthropic/claude-3.5-sonnet"

    # Azure OpenAI
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None

    # Gemini
    google_api_key: str | None = None
    gemini_model: str = "gemini-1.5-pro"

    # Data paths
    news_csv_path: str
    workspaces_path: str
    system_prompt_path: str

    @field_validator("llm_provider", mode="before")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        if v not in ("openrouter", "azure", "gemini"):
            raise ValueError(f"Invalid LLM provider: {v}")
        return v
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: add configuration module with LLM provider settings"
```

---

## Phase 2: Pydantic Models

### Task 4: Workspace Models

**Files:**
- Create: `app/models/workspace.py`
- Create: `tests/test_models_workspace.py`

**Step 1: Write the failing test**

Create `tests/test_models_workspace.py`:
```python
from datetime import datetime


def test_workspace_metadata_creation():
    """WorkspaceMetadata can be created with required fields."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-001",
        name="Test Workspace",
        created_at=datetime.now(),
    )

    assert metadata.id == "ws-001"
    assert metadata.name == "Test Workspace"
    assert metadata.description is None


def test_workspace_metadata_with_description():
    """WorkspaceMetadata can include optional description."""
    from app.models.workspace import WorkspaceMetadata

    metadata = WorkspaceMetadata(
        id="ws-002",
        name="Detailed Workspace",
        created_at=datetime.now(),
        description="A workspace for testing",
    )

    assert metadata.description == "A workspace for testing"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_workspace.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/models/workspace.py`:
```python
from datetime import datetime

from pydantic import BaseModel


class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_workspace.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/workspace.py tests/test_models_workspace.py
git commit -m "feat: add workspace metadata model"
```

---

### Task 5: Prompt Models

**Files:**
- Create: `app/models/prompts.py`
- Create: `tests/test_models_prompts.py`

**Step 1: Write the failing test**

Create `tests/test_models_prompts.py`:
```python
def test_category_definition_creation():
    """CategoryDefinition can be created."""
    from app.models.prompts import CategoryDefinition

    category = CategoryDefinition(
        name="Planned Price Sensitive",
        definition="News about scheduled corporate events that may affect stock price.",
    )

    assert category.name == "Planned Price Sensitive"
    assert "scheduled corporate events" in category.definition


def test_few_shot_example_creation():
    """FewShotExample can be created with all required fields."""
    from app.models.prompts import FewShotExample

    example = FewShotExample(
        id="ex-001",
        news_content="Company X announces Q3 earnings call scheduled for Oct 15.",
        category="Planned Price Sensitive",
        reasoning="This is a scheduled earnings announcement.",
    )

    assert example.id == "ex-001"
    assert example.category == "Planned Price Sensitive"


def test_prompt_config_holds_all_definitions():
    """PromptConfig holds list of category definitions."""
    from app.models.prompts import CategoryDefinition, PromptConfig

    config = PromptConfig(
        categories=[
            CategoryDefinition(name="Cat1", definition="Def1"),
            CategoryDefinition(name="Cat2", definition="Def2"),
        ]
    )

    assert len(config.categories) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_prompts.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/models/prompts.py`:
```python
from pydantic import BaseModel


class CategoryDefinition(BaseModel):
    name: str
    definition: str


class FewShotExample(BaseModel):
    id: str
    news_content: str
    category: str
    reasoning: str


class PromptConfig(BaseModel):
    categories: list[CategoryDefinition]


class FewShotConfig(BaseModel):
    examples: list[FewShotExample]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/prompts.py tests/test_models_prompts.py
git commit -m "feat: add prompt and few-shot models"
```

---

### Task 6: News Model

**Files:**
- Create: `app/models/news.py`
- Create: `tests/test_models_news.py`

**Step 1: Write the failing test**

Create `tests/test_models_news.py`:
```python
def test_news_article_creation():
    """NewsArticle can be created with required fields."""
    from app.models.news import NewsArticle

    article = NewsArticle(
        id="news-001",
        headline="Company X Reports Record Earnings",
        content="Full article content here...",
    )

    assert article.id == "news-001"
    assert article.headline == "Company X Reports Record Earnings"


def test_news_list_response():
    """NewsListResponse contains articles and pagination info."""
    from app.models.news import NewsArticle, NewsListResponse

    response = NewsListResponse(
        articles=[
            NewsArticle(id="1", headline="H1", content="C1"),
            NewsArticle(id="2", headline="H2", content="C2"),
        ],
        total=100,
        page=1,
        limit=20,
    )

    assert len(response.articles) == 2
    assert response.total == 100
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_news.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/models/news.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_news.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/news.py tests/test_models_news.py
git commit -m "feat: add news article models"
```

---

### Task 7: Feedback and Analysis Models

**Files:**
- Create: `app/models/feedback.py`
- Create: `tests/test_models_feedback.py`

**Step 1: Write the failing test**

Create `tests/test_models_feedback.py`:
```python
from datetime import datetime


def test_reasoning_row_creation():
    """ReasoningRow holds the 3-column reasoning data."""
    from app.models.feedback import ReasoningRow

    row = ReasoningRow(
        category_excerpt="scheduled corporate events",
        news_excerpt="Q3 earnings call scheduled",
        reasoning="Direct match with definition",
    )

    assert row.category_excerpt == "scheduled corporate events"


def test_ai_insight_creation():
    """AIInsight holds the analysis result."""
    from app.models.feedback import AIInsight, ReasoningRow

    insight = AIInsight(
        category="Planned Price Sensitive",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="excerpt1",
                news_excerpt="excerpt2",
                reasoning="reason",
            )
        ],
        confidence=0.85,
    )

    assert insight.category == "Planned Price Sensitive"
    assert insight.confidence == 0.85
    assert len(insight.reasoning_table) == 1


def test_feedback_creation():
    """Feedback captures user response to AI insight."""
    from app.models.feedback import AIInsight, Feedback, ReasoningRow

    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=False,
        correct_category="Unplanned Price Sensitive",
        reasoning="This was an unexpected announcement",
        note="The AI missed the unplanned nature",
        ai_insight=AIInsight(
            category="Planned Price Sensitive",
            reasoning_table=[],
            confidence=0.7,
        ),
        created_at=datetime.now(),
    )

    assert feedback.thumbs_up is False
    assert feedback.correct_category == "Unplanned Price Sensitive"


def test_evaluation_report_creation():
    """EvaluationReport holds the evaluation agent output."""
    from app.models.feedback import EvaluationReport, PromptGap

    report = EvaluationReport(
        id="rpt-001",
        feedback_id="fb-001",
        diagnosis="The category definition lacks clarity on timing",
        prompt_gaps=[
            PromptGap(
                location="Planned Price Sensitive definition",
                issue="Does not distinguish scheduled vs unscheduled",
                suggestion="Add clarification about pre-announced events",
            )
        ],
        few_shot_gaps=[],
        summary="Consider clarifying the timing aspect in definitions.",
    )

    assert report.diagnosis is not None
    assert len(report.prompt_gaps) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models_feedback.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/models/feedback.py`:
```python
from datetime import datetime

from pydantic import BaseModel


class ReasoningRow(BaseModel):
    category_excerpt: str
    news_excerpt: str
    reasoning: str


class AIInsight(BaseModel):
    category: str
    reasoning_table: list[ReasoningRow]
    confidence: float


class Feedback(BaseModel):
    id: str
    article_id: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    note: str
    ai_insight: AIInsight
    created_at: datetime


class PromptGap(BaseModel):
    location: str
    issue: str
    suggestion: str


class FewShotGap(BaseModel):
    example_id: str
    issue: str
    suggestion: str


class EvaluationReport(BaseModel):
    id: str
    feedback_id: str
    diagnosis: str
    prompt_gaps: list[PromptGap]
    few_shot_gaps: list[FewShotGap]
    summary: str


class ImprovementSuggestion(BaseModel):
    category_suggestions: list[dict]
    few_shot_suggestions: list[dict]
    priority_order: list[str]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models_feedback.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/feedback.py tests/test_models_feedback.py
git commit -m "feat: add feedback and evaluation report models"
```

---

## Phase 3: Services

### Task 8: Workspace Service

**Files:**
- Create: `app/services/workspace_service.py`
- Create: `tests/test_workspace_service.py`

**Step 1: Write the failing test**

Create `tests/test_workspace_service.py`:
```python
import json
from pathlib import Path

import pytest


@pytest.fixture
def workspaces_dir(tmp_path):
    """Create a temporary workspaces directory."""
    ws_dir = tmp_path / "workspaces"
    ws_dir.mkdir()
    return ws_dir


def test_create_workspace(workspaces_dir):
    """WorkspaceService creates a new workspace directory with metadata."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspace = service.create_workspace("My Workspace")

    assert workspace.name == "My Workspace"
    assert (workspaces_dir / workspace.id).exists()
    assert (workspaces_dir / workspace.id / "metadata.json").exists()


def test_list_workspaces_empty(workspaces_dir):
    """WorkspaceService returns empty list when no workspaces exist."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspaces = service.list_workspaces()

    assert workspaces == []


def test_list_workspaces_returns_all(workspaces_dir):
    """WorkspaceService lists all created workspaces."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    service.create_workspace("Workspace 1")
    service.create_workspace("Workspace 2")

    workspaces = service.list_workspaces()

    assert len(workspaces) == 2


def test_delete_workspace(workspaces_dir):
    """WorkspaceService deletes a workspace and its contents."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    workspace = service.create_workspace("To Delete")
    ws_path = workspaces_dir / workspace.id

    assert ws_path.exists()

    service.delete_workspace(workspace.id)

    assert not ws_path.exists()


def test_get_workspace(workspaces_dir):
    """WorkspaceService retrieves a workspace by ID."""
    from app.services.workspace_service import WorkspaceService

    service = WorkspaceService(workspaces_dir)
    created = service.create_workspace("Test WS")

    retrieved = service.get_workspace(created.id)

    assert retrieved.id == created.id
    assert retrieved.name == "Test WS"


def test_get_workspace_not_found(workspaces_dir):
    """WorkspaceService raises exception for non-existent workspace."""
    from app.services.workspace_service import WorkspaceService, WorkspaceNotFoundError

    service = WorkspaceService(workspaces_dir)

    with pytest.raises(WorkspaceNotFoundError):
        service.get_workspace("nonexistent-id")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace_service.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/services/workspace_service.py`:
```python
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.models.workspace import WorkspaceMetadata


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace is not found."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        super().__init__(f"Workspace not found: {workspace_id}")


class WorkspaceService:
    def __init__(self, workspaces_path: Path):
        self.workspaces_path = Path(workspaces_path)
        self.workspaces_path.mkdir(parents=True, exist_ok=True)

    def create_workspace(self, name: str) -> WorkspaceMetadata:
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        workspace_dir = self.workspaces_path / workspace_id

        workspace_dir.mkdir()
        (workspace_dir / "feedback").mkdir()
        (workspace_dir / "evaluation_reports").mkdir()

        metadata = WorkspaceMetadata(
            id=workspace_id,
            name=name,
            created_at=datetime.now(),
        )

        self._save_metadata(workspace_dir, metadata)
        self._init_empty_prompts(workspace_dir)

        return metadata

    def list_workspaces(self) -> list[WorkspaceMetadata]:
        workspaces = []
        for ws_dir in self.workspaces_path.iterdir():
            if ws_dir.is_dir() and (ws_dir / "metadata.json").exists():
                workspaces.append(self._load_metadata(ws_dir))
        return sorted(workspaces, key=lambda w: w.created_at, reverse=True)

    def get_workspace(self, workspace_id: str) -> WorkspaceMetadata:
        workspace_dir = self.workspaces_path / workspace_id
        if not workspace_dir.exists():
            raise WorkspaceNotFoundError(workspace_id)
        return self._load_metadata(workspace_dir)

    def delete_workspace(self, workspace_id: str) -> None:
        workspace_dir = self.workspaces_path / workspace_id
        if not workspace_dir.exists():
            raise WorkspaceNotFoundError(workspace_id)
        shutil.rmtree(workspace_dir)

    def _save_metadata(self, workspace_dir: Path, metadata: WorkspaceMetadata) -> None:
        with open(workspace_dir / "metadata.json", "w") as f:
            json.dump(metadata.model_dump(mode="json"), f, indent=2)

    def _load_metadata(self, workspace_dir: Path) -> WorkspaceMetadata:
        with open(workspace_dir / "metadata.json") as f:
            return WorkspaceMetadata.model_validate(json.load(f))

    def _init_empty_prompts(self, workspace_dir: Path) -> None:
        with open(workspace_dir / "category_definitions.json", "w") as f:
            json.dump({"categories": []}, f)
        with open(workspace_dir / "few_shot_examples.json", "w") as f:
            json.dump({"examples": []}, f)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/workspace_service.py tests/test_workspace_service.py
git commit -m "feat: add workspace service for CRUD operations"
```

---

### Task 9: News Service

**Files:**
- Create: `app/services/news_service.py`
- Create: `tests/test_news_service.py`

**Step 1: Write the failing test**

Create `tests/test_news_service.py`:
```python
import csv
from pathlib import Path

import pytest


@pytest.fixture
def news_csv(tmp_path):
    """Create a temporary news CSV file."""
    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        for i in range(50):
            writer.writerow({
                "id": f"news-{i:03d}",
                "headline": f"Headline {i}",
                "content": f"Content for article {i}",
            })
    return csv_path


def test_get_news_paginated(news_csv):
    """NewsService returns paginated news articles."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=1, limit=10)

    assert len(response.articles) == 10
    assert response.total == 50
    assert response.page == 1
    assert response.limit == 10


def test_get_news_second_page(news_csv):
    """NewsService returns correct page of articles."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=2, limit=10)

    assert len(response.articles) == 10
    assert response.articles[0].id == "news-010"


def test_get_news_last_partial_page(news_csv):
    """NewsService handles partial last page correctly."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    response = service.get_news(page=3, limit=20)

    assert len(response.articles) == 10  # 50 total, page 3 of 20 = remaining 10


def test_get_article_by_id(news_csv):
    """NewsService retrieves a single article by ID."""
    from app.services.news_service import NewsService

    service = NewsService(news_csv)
    article = service.get_article("news-025")

    assert article.id == "news-025"
    assert article.headline == "Headline 25"


def test_get_article_not_found(news_csv):
    """NewsService raises exception for non-existent article."""
    from app.services.news_service import NewsService, ArticleNotFoundError

    service = NewsService(news_csv)

    with pytest.raises(ArticleNotFoundError):
        service.get_article("nonexistent")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_news_service.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/services/news_service.py`:
```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_news_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/news_service.py tests/test_news_service.py
git commit -m "feat: add news service for CSV reading and pagination"
```

---

### Task 10: Prompt Service

**Files:**
- Create: `app/services/prompt_service.py`
- Create: `tests/test_prompt_service.py`

**Step 1: Write the failing test**

Create `tests/test_prompt_service.py`:
```python
import json
from pathlib import Path

import pytest


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory with empty prompts."""
    ws_dir = tmp_path / "ws-test"
    ws_dir.mkdir()
    with open(ws_dir / "category_definitions.json", "w") as f:
        json.dump({"categories": []}, f)
    with open(ws_dir / "few_shot_examples.json", "w") as f:
        json.dump({"examples": []}, f)
    return ws_dir


def test_get_categories_empty(workspace_dir):
    """PromptService returns empty categories initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_categories()

    assert config.categories == []


def test_save_categories(workspace_dir):
    """PromptService saves category definitions."""
    from app.models.prompts import CategoryDefinition, PromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = PromptConfig(categories=[
        CategoryDefinition(name="Cat1", definition="Def1"),
    ])

    service.save_categories(config)
    loaded = service.get_categories()

    assert len(loaded.categories) == 1
    assert loaded.categories[0].name == "Cat1"


def test_get_few_shots_empty(workspace_dir):
    """PromptService returns empty few-shots initially."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_few_shots()

    assert config.examples == []


def test_save_few_shots(workspace_dir):
    """PromptService saves few-shot examples."""
    from app.models.prompts import FewShotConfig, FewShotExample
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = FewShotConfig(examples=[
        FewShotExample(
            id="ex-001",
            news_content="Test news",
            category="Cat1",
            reasoning="Test reasoning",
        ),
    ])

    service.save_few_shots(config)
    loaded = service.get_few_shots()

    assert len(loaded.examples) == 1
    assert loaded.examples[0].id == "ex-001"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompt_service.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/services/prompt_service.py`:
```python
import json
from pathlib import Path

from app.models.prompts import FewShotConfig, PromptConfig


class PromptService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.categories_file = self.workspace_dir / "category_definitions.json"
        self.few_shots_file = self.workspace_dir / "few_shot_examples.json"

    def get_categories(self) -> PromptConfig:
        with open(self.categories_file) as f:
            return PromptConfig.model_validate(json.load(f))

    def save_categories(self, config: PromptConfig) -> None:
        with open(self.categories_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)

    def get_few_shots(self) -> FewShotConfig:
        with open(self.few_shots_file) as f:
            return FewShotConfig.model_validate(json.load(f))

    def save_few_shots(self, config: FewShotConfig) -> None:
        with open(self.few_shots_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_prompt_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/prompt_service.py tests/test_prompt_service.py
git commit -m "feat: add prompt service for category and few-shot management"
```

---

### Task 11: Feedback Service

**Files:**
- Create: `app/services/feedback_service.py`
- Create: `tests/test_feedback_service.py`

**Step 1: Write the failing test**

Create `tests/test_feedback_service.py`:
```python
import json
from datetime import datetime
from pathlib import Path

import pytest


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a workspace directory with feedback folders."""
    ws_dir = tmp_path / "ws-test"
    ws_dir.mkdir()
    (ws_dir / "feedback").mkdir()
    (ws_dir / "evaluation_reports").mkdir()
    return ws_dir


def test_save_feedback(workspace_dir):
    """FeedbackService saves feedback to disk."""
    from app.models.feedback import AIInsight, Feedback
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=True,
        correct_category="Cat1",
        reasoning="Good",
        note="Accurate",
        ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.9),
        created_at=datetime.now(),
    )

    service.save_feedback(feedback)

    assert (workspace_dir / "feedback" / "fb-001.json").exists()


def test_list_feedback(workspace_dir):
    """FeedbackService lists all feedback for workspace."""
    from app.models.feedback import AIInsight, Feedback
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    for i in range(3):
        feedback = Feedback(
            id=f"fb-{i:03d}",
            article_id=f"news-{i:03d}",
            thumbs_up=True,
            correct_category="Cat1",
            reasoning="Good",
            note="Note",
            ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.9),
            created_at=datetime.now(),
        )
        service.save_feedback(feedback)

    feedbacks = service.list_feedback()

    assert len(feedbacks) == 3


def test_save_evaluation_report(workspace_dir):
    """FeedbackService saves evaluation report to disk."""
    from app.models.feedback import EvaluationReport
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    report = EvaluationReport(
        id="rpt-001",
        feedback_id="fb-001",
        diagnosis="Test diagnosis",
        prompt_gaps=[],
        few_shot_gaps=[],
        summary="Test summary",
    )

    service.save_evaluation_report(report)

    assert (workspace_dir / "evaluation_reports" / "rpt-001.json").exists()


def test_list_evaluation_reports(workspace_dir):
    """FeedbackService lists all evaluation reports."""
    from app.models.feedback import EvaluationReport
    from app.services.feedback_service import FeedbackService

    service = FeedbackService(workspace_dir)
    for i in range(2):
        report = EvaluationReport(
            id=f"rpt-{i:03d}",
            feedback_id=f"fb-{i:03d}",
            diagnosis="Diagnosis",
            prompt_gaps=[],
            few_shot_gaps=[],
            summary="Summary",
        )
        service.save_evaluation_report(report)

    reports = service.list_evaluation_reports()

    assert len(reports) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_feedback_service.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/services/feedback_service.py`:
```python
import json
from pathlib import Path

from app.models.feedback import EvaluationReport, Feedback


class FeedbackService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.feedback_dir = self.workspace_dir / "feedback"
        self.reports_dir = self.workspace_dir / "evaluation_reports"

    def save_feedback(self, feedback: Feedback) -> None:
        file_path = self.feedback_dir / f"{feedback.id}.json"
        with open(file_path, "w") as f:
            json.dump(feedback.model_dump(mode="json"), f, indent=2)

    def list_feedback(self) -> list[Feedback]:
        feedbacks = []
        for file_path in self.feedback_dir.glob("*.json"):
            with open(file_path) as f:
                feedbacks.append(Feedback.model_validate(json.load(f)))
        return sorted(feedbacks, key=lambda fb: fb.created_at, reverse=True)

    def save_evaluation_report(self, report: EvaluationReport) -> None:
        file_path = self.reports_dir / f"{report.id}.json"
        with open(file_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2)

    def list_evaluation_reports(self) -> list[EvaluationReport]:
        reports = []
        for file_path in self.reports_dir.glob("*.json"):
            with open(file_path) as f:
                reports.append(EvaluationReport.model_validate(json.load(f)))
        return reports
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_feedback_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/feedback_service.py tests/test_feedback_service.py
git commit -m "feat: add feedback service for persisting feedback and reports"
```

---

## Phase 4: LLM Agents

### Task 12: LLM Provider Factory

**Files:**
- Create: `app/agents/llm_provider.py`
- Create: `tests/test_llm_provider.py`

**Step 1: Write the failing test**

Create `tests/test_llm_provider.py`:
```python
import pytest


def test_get_openrouter_llm(monkeypatch):
    """LLMProvider returns OpenRouter LLM when configured."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.agents.llm_provider import get_llm
    from app.config import Settings

    settings = Settings()
    llm = get_llm(settings)

    assert llm is not None


def test_get_llm_missing_api_key(monkeypatch):
    """LLMProvider raises error when API key missing."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("NEWS_CSV_PATH", "./data/news.csv")
    monkeypatch.setenv("WORKSPACES_PATH", "./data/workspaces")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./prompts/system_prompt.txt")

    from app.agents.llm_provider import get_llm, LLMConfigurationError
    from app.config import Settings

    settings = Settings()

    with pytest.raises(LLMConfigurationError):
        get_llm(settings)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_llm_provider.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/agents/llm_provider.py`:
```python
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import Settings


class LLMConfigurationError(Exception):
    """Raised when LLM is not properly configured."""
    pass


def get_llm(settings: Settings):
    """Factory function to create LLM based on configuration."""
    if settings.llm_provider == "openrouter":
        if not settings.openrouter_api_key:
            raise LLMConfigurationError("OPENROUTER_API_KEY is required")
        return ChatOpenAI(
            model=settings.openrouter_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
        )
    elif settings.llm_provider == "azure":
        if not settings.azure_openai_api_key:
            raise LLMConfigurationError("AZURE_OPENAI_API_KEY is required")
        if not settings.azure_openai_endpoint:
            raise LLMConfigurationError("AZURE_OPENAI_ENDPOINT is required")
        if not settings.azure_openai_deployment:
            raise LLMConfigurationError("AZURE_OPENAI_DEPLOYMENT is required")
        return ChatOpenAI(
            model=settings.azure_openai_deployment,
            openai_api_key=settings.azure_openai_api_key,
            openai_api_base=settings.azure_openai_endpoint,
        )
    elif settings.llm_provider == "gemini":
        if not settings.google_api_key:
            raise LLMConfigurationError("GOOGLE_API_KEY is required")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
        )
    else:
        raise LLMConfigurationError(f"Unknown LLM provider: {settings.llm_provider}")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_llm_provider.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/llm_provider.py tests/test_llm_provider.py
git commit -m "feat: add LLM provider factory for OpenRouter/Azure/Gemini"
```

---

### Task 13: Analysis Agent

**Files:**
- Create: `app/agents/analysis_agent.py`
- Create: `tests/test_analysis_agent.py`

**Step 1: Write the failing test**

Create `tests/test_analysis_agent.py`:
```python
from unittest.mock import MagicMock

import pytest


def test_analysis_agent_builds_prompt():
    """AnalysisAgent builds prompt from all three dimensions."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [
        CategoryDefinition(name="Cat1", definition="Definition 1"),
    ]
    few_shots = [
        FewShotExample(id="ex1", news_content="News 1", category="Cat1", reasoning="R1"),
    ]

    prompt = agent._build_prompt(categories, few_shots, "Test article content")

    assert "You are an analyst." in prompt
    assert "Cat1" in prompt
    assert "Definition 1" in prompt
    assert "News 1" in prompt
    assert "Test article content" in prompt


def test_analysis_agent_parses_response():
    """AnalysisAgent parses LLM response into AIInsight."""
    from app.agents.analysis_agent import AnalysisAgent

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="Test")

    raw_response = '''{
        "category": "Cat1",
        "reasoning_table": [
            {"category_excerpt": "exc1", "news_excerpt": "exc2", "reasoning": "r1"}
        ],
        "confidence": 0.85
    }'''

    insight = agent._parse_response(raw_response)

    assert insight.category == "Cat1"
    assert insight.confidence == 0.85
    assert len(insight.reasoning_table) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_analysis_agent.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/agents/analysis_agent.py`:
```python
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import AIInsight, ReasoningRow
from app.models.prompts import CategoryDefinition, FewShotExample


class AnalysisAgent:
    def __init__(self, llm: BaseChatModel, system_prompt: str):
        self.llm = llm
        self.system_prompt = system_prompt

    def analyze(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
    ) -> AIInsight:
        prompt = self._build_prompt(categories, few_shots, article_content)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
    ) -> str:
        parts = [self.system_prompt, "\n\n## Category Definitions\n"]

        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n")

        if few_shots:
            parts.append("\n## Examples\n")
            for ex in few_shots:
                parts.append(f"**News:** {ex.news_content}\n")
                parts.append(f"**Category:** {ex.category}\n")
                parts.append(f"**Reasoning:** {ex.reasoning}\n\n")

        parts.append("\n## Article to Analyze\n")
        parts.append(article_content)
        parts.append("\n\n## Instructions\n")
        parts.append("Respond with a JSON object containing:\n")
        parts.append("- category: the category name\n")
        parts.append("- reasoning_table: array of {category_excerpt, news_excerpt, reasoning}\n")
        parts.append("- confidence: float between 0 and 1\n")

        return "".join(parts)

    def _parse_response(self, response: str) -> AIInsight:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        return AIInsight(
            category=data["category"],
            reasoning_table=[
                ReasoningRow(**row) for row in data["reasoning_table"]
            ],
            confidence=data["confidence"],
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_analysis_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/analysis_agent.py tests/test_analysis_agent.py
git commit -m "feat: add analysis agent for news classification"
```

---

### Task 14: Evaluation Agent

**Files:**
- Create: `app/agents/evaluation_agent.py`
- Create: `tests/test_evaluation_agent.py`

**Step 1: Write the failing test**

Create `tests/test_evaluation_agent.py`:
```python
from datetime import datetime
from unittest.mock import MagicMock

import pytest


def test_evaluation_agent_builds_prompt():
    """EvaluationAgent builds prompt with feedback context."""
    from app.agents.evaluation_agent import EvaluationAgent
    from app.models.feedback import AIInsight, Feedback
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = EvaluationAgent(llm=mock_llm)

    feedback = Feedback(
        id="fb-001",
        article_id="news-001",
        thumbs_up=False,
        correct_category="Cat2",
        reasoning="Wrong category",
        note="Should be Cat2",
        ai_insight=AIInsight(category="Cat1", reasoning_table=[], confidence=0.8),
        created_at=datetime.now(),
    )
    categories = [CategoryDefinition(name="Cat1", definition="Def1")]
    few_shots = []

    prompt = agent._build_prompt(feedback, categories, few_shots)

    assert "Cat1" in prompt
    assert "Cat2" in prompt
    assert "thumbs_up: False" in prompt or "negative" in prompt.lower()


def test_evaluation_agent_parses_response():
    """EvaluationAgent parses LLM response into EvaluationReport."""
    from app.agents.evaluation_agent import EvaluationAgent

    mock_llm = MagicMock()
    agent = EvaluationAgent(llm=mock_llm)

    raw_response = '''{
        "diagnosis": "Category definition unclear",
        "prompt_gaps": [{"location": "Cat1", "issue": "Vague", "suggestion": "Clarify"}],
        "few_shot_gaps": [],
        "summary": "Improve Cat1 definition"
    }'''

    report = agent._parse_response("fb-001", raw_response)

    assert report.feedback_id == "fb-001"
    assert report.diagnosis == "Category definition unclear"
    assert len(report.prompt_gaps) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_evaluation_agent.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/agents/evaluation_agent.py`:
```python
import json
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import (
    EvaluationReport,
    Feedback,
    FewShotGap,
    PromptGap,
)
from app.models.prompts import CategoryDefinition, FewShotExample


EVALUATION_SYSTEM_PROMPT = """You are a prompt evaluation expert. Your task is to analyze why an AI classification was correct or incorrect, and identify gaps in the prompt configuration.

Analyze the provided feedback and identify:
1. What caused the correct/incorrect classification
2. Gaps or issues in category definitions
3. Gaps or issues in few-shot examples

Respond with a JSON object containing:
- diagnosis: string explaining what went right/wrong
- prompt_gaps: array of {location, issue, suggestion}
- few_shot_gaps: array of {example_id, issue, suggestion}
- summary: concise actionable summary for the user
"""


class EvaluationAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def evaluate(
        self,
        feedback: Feedback,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> EvaluationReport:
        prompt = self._build_prompt(feedback, categories, few_shots)
        messages = [
            SystemMessage(content=EVALUATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(feedback.id, response.content)

    def _build_prompt(
        self,
        feedback: Feedback,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## Feedback Details\n"]
        parts.append(f"- Thumbs up: {feedback.thumbs_up}\n")
        parts.append(f"- AI predicted: {feedback.ai_insight.category}\n")
        parts.append(f"- Correct category: {feedback.correct_category}\n")
        parts.append(f"- User reasoning: {feedback.reasoning}\n")
        parts.append(f"- User note: {feedback.note}\n\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"- ID: {ex.id}, Category: {ex.category}\n")
                parts.append(f"  Content: {ex.news_content[:100]}...\n\n")

        return "".join(parts)

    def _parse_response(self, feedback_id: str, response: str) -> EvaluationReport:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        return EvaluationReport(
            id=f"rpt-{uuid.uuid4().hex[:8]}",
            feedback_id=feedback_id,
            diagnosis=data["diagnosis"],
            prompt_gaps=[PromptGap(**gap) for gap in data.get("prompt_gaps", [])],
            few_shot_gaps=[FewShotGap(**gap) for gap in data.get("few_shot_gaps", [])],
            summary=data["summary"],
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_evaluation_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/evaluation_agent.py tests/test_evaluation_agent.py
git commit -m "feat: add evaluation agent for feedback analysis"
```

---

### Task 15: Improvement Agent

**Files:**
- Create: `app/agents/improvement_agent.py`
- Create: `tests/test_improvement_agent.py`

**Step 1: Write the failing test**

Create `tests/test_improvement_agent.py`:
```python
from unittest.mock import MagicMock

import pytest


def test_improvement_agent_builds_prompt():
    """ImprovementAgent builds prompt from all reports."""
    from app.agents.improvement_agent import ImprovementAgent
    from app.models.feedback import EvaluationReport, PromptGap
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    reports = [
        EvaluationReport(
            id="rpt-001",
            feedback_id="fb-001",
            diagnosis="Issue 1",
            prompt_gaps=[PromptGap(location="Cat1", issue="Vague", suggestion="Fix")],
            few_shot_gaps=[],
            summary="Summary 1",
        ),
    ]
    categories = [CategoryDefinition(name="Cat1", definition="Def1")]

    prompt = agent._build_prompt(reports, categories, [])

    assert "Issue 1" in prompt
    assert "Cat1" in prompt


def test_improvement_agent_parses_response():
    """ImprovementAgent parses response into suggestions."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [{"category": "Cat1", "current": "Def1", "suggested": "Better def", "rationale": "Clearer"}],
        "few_shot_suggestions": [],
        "priority_order": ["Fix Cat1 first"]
    }'''

    result = agent._parse_response(raw_response)

    assert len(result.category_suggestions) == 1
    assert result.priority_order[0] == "Fix Cat1 first"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_improvement_agent.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/agents/improvement_agent.py`:
```python
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import EvaluationReport, ImprovementSuggestion
from app.models.prompts import CategoryDefinition, FewShotExample


IMPROVEMENT_SYSTEM_PROMPT = """You are a prompt optimization expert. Analyze the evaluation reports and suggest improvements to category definitions and few-shot examples.

Focus on:
1. Patterns across multiple reports
2. Recurring issues in definitions
3. Missing or misleading few-shot examples

Respond with a JSON object containing:
- category_suggestions: array of {category, current, suggested, rationale}
- few_shot_suggestions: array of {action: "add"|"modify"|"remove", details}
- priority_order: array of strings indicating what to fix first
"""


class ImprovementAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def suggest_improvements(
        self,
        reports: list[EvaluationReport],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> ImprovementSuggestion:
        prompt = self._build_prompt(reports, categories, few_shots)
        messages = [
            SystemMessage(content=IMPROVEMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        reports: list[EvaluationReport],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## Evaluation Reports Summary\n\n"]

        for report in reports:
            parts.append(f"### Report {report.id}\n")
            parts.append(f"- Diagnosis: {report.diagnosis}\n")
            parts.append(f"- Summary: {report.summary}\n")
            if report.prompt_gaps:
                parts.append("- Prompt gaps:\n")
                for gap in report.prompt_gaps:
                    parts.append(f"  - {gap.location}: {gap.issue}\n")
            parts.append("\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"- {ex.id}: {ex.category} - {ex.news_content[:50]}...\n")

        return "".join(parts)

    def _parse_response(self, response: str) -> ImprovementSuggestion:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())
        return ImprovementSuggestion(
            category_suggestions=data.get("category_suggestions", []),
            few_shot_suggestions=data.get("few_shot_suggestions", []),
            priority_order=data.get("priority_order", []),
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_improvement_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/improvement_agent.py tests/test_improvement_agent.py
git commit -m "feat: add improvement agent for batch prompt suggestions"
```

---

## Phase 5: FastAPI Routes

### Task 16: FastAPI App Setup

**Files:**
- Create: `app/main.py`
- Create: `app/dependencies.py`

**Step 1: Create dependencies module**

Create `app/dependencies.py`:
```python
from functools import lru_cache
from pathlib import Path

from app.config import Settings
from app.services.workspace_service import WorkspaceService
from app.services.news_service import NewsService
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


def get_system_prompt() -> str:
    settings = get_settings()
    with open(settings.system_prompt_path) as f:
        return f.read()
```

**Step 2: Create main FastAPI app**

Create `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import pages, workspaces, news, prompts, workflows

app = FastAPI(title="Prompt Enhancer", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

```bash
git add app/main.py app/dependencies.py
git commit -m "feat: add FastAPI app setup with dependencies"
```

---

### Task 17: Workspace Routes

**Files:**
- Create: `app/routes/workspaces.py`
- Create: `tests/test_routes_workspaces.py`

**Step 1: Write the failing test**

Create `tests/test_routes_workspaces.py`:
```python
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

    # Create required files
    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.main import app
    return TestClient(app)


def test_create_workspace(client):
    """POST /api/workspaces creates a new workspace."""
    response = client.post("/api/workspaces", json={"name": "Test Workspace"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workspace"
    assert "id" in data


def test_list_workspaces(client):
    """GET /api/workspaces returns all workspaces."""
    client.post("/api/workspaces", json={"name": "WS1"})
    client.post("/api/workspaces", json={"name": "WS2"})

    response = client.get("/api/workspaces")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_delete_workspace(client):
    """DELETE /api/workspaces/{id} removes workspace."""
    create_response = client.post("/api/workspaces", json={"name": "To Delete"})
    workspace_id = create_response.json()["id"]

    response = client.delete(f"/api/workspaces/{workspace_id}")

    assert response.status_code == 204

    list_response = client.get("/api/workspaces")
    assert len(list_response.json()) == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_workspaces.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/routes/workspaces.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_workspace_service
from app.models.workspace import WorkspaceMetadata
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkspaceMetadata)
def create_workspace(
    request: CreateWorkspaceRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.create_workspace(request.name)


@router.get("", response_model=list[WorkspaceMetadata])
def list_workspaces(service: WorkspaceService = Depends(get_workspace_service)):
    return service.list_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceMetadata)
def get_workspace(
    workspace_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        return service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        service.delete_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_workspaces.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workspaces.py tests/test_routes_workspaces.py
git commit -m "feat: add workspace API routes"
```

---

### Task 18: News Routes

**Files:**
- Create: `app/routes/news.py`
- Create: `tests/test_routes_news.py`

**Step 1: Write the failing test**

Create `tests/test_routes_news.py`:
```python
import csv

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with sample news data."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))

    # Create news CSV with sample data
    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        for i in range(25):
            writer.writerow({
                "id": f"news-{i:03d}",
                "headline": f"Headline {i}",
                "content": f"Content {i}",
            })

    monkeypatch.setenv("NEWS_CSV_PATH", str(csv_path))
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.main import app
    return TestClient(app)


def test_get_news_paginated(client):
    """GET /api/news returns paginated news."""
    response = client.get("/api/news?page=1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert len(data["articles"]) == 10
    assert data["total"] == 25
    assert data["page"] == 1


def test_get_news_second_page(client):
    """GET /api/news returns correct page."""
    response = client.get("/api/news?page=2&limit=10")

    data = response.json()
    assert data["articles"][0]["id"] == "news-010"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_news.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/routes/news.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_news_service
from app.models.news import NewsArticle, NewsListResponse
from app.services.news_service import ArticleNotFoundError, NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=NewsListResponse)
def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
):
    return service.get_news(page=page, limit=limit)


@router.get("/{article_id}", response_model=NewsArticle)
def get_article(
    article_id: str,
    service: NewsService = Depends(get_news_service),
):
    try:
        return service.get_article(article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_news.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/news.py tests/test_routes_news.py
git commit -m "feat: add news API routes with pagination"
```

---

### Task 19: Prompt Routes

**Files:**
- Create: `app/routes/prompts.py`
- Create: `tests/test_routes_prompts.py`

**Step 1: Write the failing test**

Create `tests/test_routes_prompts.py`:
```python
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with workspace."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("NEWS_CSV_PATH", str(tmp_path / "news.csv"))
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))

    (tmp_path / "news.csv").write_text("id,headline,content\n")
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.main import app
    return TestClient(app)


@pytest.fixture
def workspace_id(client):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json={"name": "Test"})
    return response.json()["id"]


def test_get_categories_empty(client, workspace_id):
    """GET categories returns empty list initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/categories")

    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_save_categories(client, workspace_id):
    """PUT categories saves and returns categories."""
    categories = {
        "categories": [
            {"name": "Cat1", "definition": "Definition 1"}
        ]
    }

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/categories",
        json=categories,
    )

    assert response.status_code == 200
    assert len(response.json()["categories"]) == 1


def test_get_few_shots_empty(client, workspace_id):
    """GET few-shots returns empty list initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/few-shots")

    assert response.status_code == 200
    assert response.json()["examples"] == []


def test_save_few_shots(client, workspace_id):
    """PUT few-shots saves and returns examples."""
    few_shots = {
        "examples": [
            {
                "id": "ex-001",
                "news_content": "Test news",
                "category": "Cat1",
                "reasoning": "Test reasoning",
            }
        ]
    }

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/few-shots",
        json=few_shots,
    )

    assert response.status_code == 200
    assert len(response.json()["examples"]) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_prompts.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/routes/prompts.py`:
```python
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_settings, get_workspace_service
from app.models.prompts import FewShotConfig, PromptConfig
from app.services.prompt_service import PromptService
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces/{workspace_id}/prompts", tags=["prompts"])


def get_prompt_service(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> PromptService:
    settings = get_settings()
    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")
    workspace_dir = Path(settings.workspaces_path) / workspace_id
    return PromptService(workspace_dir)


@router.get("/categories", response_model=PromptConfig)
def get_categories(service: PromptService = Depends(get_prompt_service)):
    return service.get_categories()


@router.put("/categories", response_model=PromptConfig)
def save_categories(
    config: PromptConfig,
    service: PromptService = Depends(get_prompt_service),
):
    service.save_categories(config)
    return config


@router.get("/few-shots", response_model=FewShotConfig)
def get_few_shots(service: PromptService = Depends(get_prompt_service)):
    return service.get_few_shots()


@router.put("/few-shots", response_model=FewShotConfig)
def save_few_shots(
    config: FewShotConfig,
    service: PromptService = Depends(get_prompt_service),
):
    service.save_few_shots(config)
    return config
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/prompts.py tests/test_routes_prompts.py
git commit -m "feat: add prompt API routes for categories and few-shots"
```

---

### Task 20: Workflow Routes

**Files:**
- Create: `app/routes/workflows.py`
- Create: `tests/test_routes_workflows.py`

**Step 1: Write the failing test**

Create `tests/test_routes_workflows.py`:
```python
import csv
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create test client with workspace and news."""
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("WORKSPACES_PATH", str(tmp_path / "workspaces"))
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(tmp_path / "system.txt"))

    csv_path = tmp_path / "news.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "headline", "content"])
        writer.writeheader()
        writer.writerow({"id": "news-001", "headline": "Test", "content": "Content"})

    monkeypatch.setenv("NEWS_CSV_PATH", str(csv_path))
    (tmp_path / "workspaces").mkdir()
    (tmp_path / "system.txt").write_text("Test prompt")

    from app.main import app
    return TestClient(app)


@pytest.fixture
def workspace_id(client):
    """Create workspace with categories."""
    response = client.post("/api/workspaces", json={"name": "Test"})
    ws_id = response.json()["id"]

    # Add categories
    client.put(
        f"/api/workspaces/{ws_id}/prompts/categories",
        json={"categories": [{"name": "Cat1", "definition": "Def1"}]},
    )
    return ws_id


def test_analyze_article(client, workspace_id):
    """POST /api/workspaces/{id}/analyze runs analysis agent."""
    mock_insight = {
        "category": "Cat1",
        "reasoning_table": [],
        "confidence": 0.9,
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = str(mock_insight).replace("'", '"')
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/analyze",
            json={"article_id": "news-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "category" in data


def test_submit_feedback(client, workspace_id):
    """POST /api/workspaces/{id}/feedback saves feedback and runs evaluation."""
    mock_report = {
        "diagnosis": "Test",
        "prompt_gaps": [],
        "few_shot_gaps": [],
        "summary": "Test summary",
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = str(mock_report).replace("'", '"')
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/feedback",
            json={
                "article_id": "news-001",
                "thumbs_up": True,
                "correct_category": "Cat1",
                "reasoning": "Correct",
                "note": "Good",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.9,
                },
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_routes_workflows.py -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

Create `app/routes/workflows.py`:
```python
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agents.analysis_agent import AnalysisAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.improvement_agent import ImprovementAgent
from app.agents.llm_provider import get_llm
from app.dependencies import get_news_service, get_settings, get_workspace_service
from app.models.feedback import AIInsight, EvaluationReport, Feedback, ImprovementSuggestion
from app.services.feedback_service import FeedbackService
from app.services.news_service import ArticleNotFoundError, NewsService
from app.services.prompt_service import PromptService
from app.services.workspace_service import WorkspaceNotFoundError, WorkspaceService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["workflows"])


class AnalyzeRequest(BaseModel):
    article_id: str


class FeedbackRequest(BaseModel):
    article_id: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    note: str
    ai_insight: AIInsight


@router.post("/analyze", response_model=AIInsight)
def analyze_article(
    workspace_id: str,
    request: AnalyzeRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    news_service: NewsService = Depends(get_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        article = news_service.get_article(request.article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    with open(settings.system_prompt_path) as f:
        system_prompt = f.read()

    llm = get_llm(settings)
    agent = AnalysisAgent(llm=llm, system_prompt=system_prompt)

    return agent.analyze(categories, few_shots, article.content)


@router.post("/feedback", response_model=EvaluationReport)
def submit_feedback(
    workspace_id: str,
    request: FeedbackRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)
    feedback_service = FeedbackService(workspace_dir)

    feedback = Feedback(
        id=f"fb-{uuid.uuid4().hex[:8]}",
        article_id=request.article_id,
        thumbs_up=request.thumbs_up,
        correct_category=request.correct_category,
        reasoning=request.reasoning,
        note=request.note,
        ai_insight=request.ai_insight,
        created_at=datetime.now(),
    )
    feedback_service.save_feedback(feedback)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples

    llm = get_llm(settings)
    agent = EvaluationAgent(llm=llm)
    report = agent.evaluate(feedback, categories, few_shots)

    feedback_service.save_evaluation_report(report)

    return report


@router.get("/feedback", response_model=list[Feedback])
def list_feedback(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    feedback_service = FeedbackService(workspace_dir)

    return feedback_service.list_feedback()


@router.post("/suggest-improvements", response_model=ImprovementSuggestion)
def suggest_improvements(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)
    feedback_service = FeedbackService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples
    reports = feedback_service.list_evaluation_reports()

    if not reports:
        raise HTTPException(status_code=400, detail="No evaluation reports available")

    llm = get_llm(settings)
    agent = ImprovementAgent(llm=llm)

    return agent.suggest_improvements(reports, categories, few_shots)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_routes_workflows.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workflows.py tests/test_routes_workflows.py
git commit -m "feat: add workflow routes for analyze, feedback, and suggestions"
```

---

### Task 21: Page Routes (HTML)

**Files:**
- Create: `app/routes/pages.py`

**Step 1: Create page routes**

Create `app/routes/pages.py`:
```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_workspace_service
from app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def news_list_page(
    request: Request,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces()
    return templates.TemplateResponse(
        "news_list.html",
        {"request": request, "workspaces": workspaces},
    )


@router.get("/prompts", response_class=HTMLResponse)
def prompts_page(
    request: Request,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = workspace_service.list_workspaces()
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, "workspaces": workspaces},
    )
```

**Step 2: Commit**

```bash
git add app/routes/pages.py
git commit -m "feat: add HTML page routes"
```

---

## Phase 6: UI Templates

### Task 22: Base Template

**Files:**
- Create: `app/templates/base.html`

**Step 1: Create base template with Tailwind and HTMX**

Create `app/templates/base.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Prompt Enhancer{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-white shadow">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <a href="/" class="text-xl font-bold text-gray-900">Prompt Enhancer</a>
            <nav class="flex items-center gap-4">
                <a href="/" class="text-gray-600 hover:text-gray-900">News</a>
                <a href="/prompts" class="text-gray-600 hover:text-gray-900">Prompts</a>
                <div class="flex items-center gap-2">
                    <select id="workspace-selector"
                            class="border rounded px-3 py-1.5 text-sm"
                            hx-get="/api/workspaces"
                            hx-trigger="load">
                        <option value="">Select Workspace</option>
                        {% for ws in workspaces %}
                        <option value="{{ ws.id }}">{{ ws.name }}</option>
                        {% endfor %}
                    </select>
                    <button onclick="createWorkspace()"
                            class="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700">
                        + New
                    </button>
                </div>
            </nav>
        </div>
    </header>
    <main class="max-w-7xl mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </main>
    <script>
        function getWorkspaceId() {
            return document.getElementById('workspace-selector').value;
        }

        function createWorkspace() {
            const name = prompt('Workspace name:');
            if (name) {
                fetch('/api/workspaces', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name})
                }).then(() => location.reload());
            }
        }
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step 2: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: add base HTML template with HTMX and Tailwind"
```

---

### Task 23: News List Template

**Files:**
- Create: `app/templates/news_list.html`
- Create: `app/templates/partials/news_row.html`
- Create: `app/templates/partials/ai_insight.html`

**Step 1: Create news list template**

Create `app/templates/news_list.html`:
```html
{% extends "base.html" %}

{% block title %}News - Prompt Enhancer{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">News Articles</h1>
    <button onclick="suggestImprovements()"
            class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
        Suggest Prompt Improvements
    </button>
</div>

<div id="news-list" class="space-y-4"
     hx-get="/api/news?page=1&limit=20"
     hx-trigger="load"
     hx-swap="innerHTML">
    <div class="text-center py-8 text-gray-500">Loading news...</div>
</div>

<div id="suggestions-modal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
        <h2 class="text-xl font-bold mb-4">Prompt Improvement Suggestions</h2>
        <div id="suggestions-content"></div>
        <button onclick="closeSuggestionsModal()" class="mt-4 bg-gray-600 text-white px-4 py-2 rounded">Close</button>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    function startWorkflow(articleId) {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }
        const row = document.getElementById('row-' + articleId);
        const insightDiv = row.querySelector('.ai-insight');
        insightDiv.innerHTML = '<div class="p-4 text-gray-500">Analyzing...</div>';
        insightDiv.classList.remove('hidden');

        fetch(`/api/workspaces/${wsId}/analyze`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({article_id: articleId})
        })
        .then(r => r.json())
        .then(data => {
            insightDiv.innerHTML = renderInsight(articleId, data);
        })
        .catch(err => {
            insightDiv.innerHTML = '<div class="p-4 text-red-500">Error: ' + err.message + '</div>';
        });
    }

    function renderInsight(articleId, insight) {
        return `
            <div class="p-4 bg-blue-50 border-t">
                <h4 class="font-semibold">AI Insight</h4>
                <p><strong>Category:</strong> ${insight.category}</p>
                <p><strong>Confidence:</strong> ${(insight.confidence * 100).toFixed(0)}%</p>
                <table class="w-full mt-2 text-sm border">
                    <thead><tr class="bg-gray-100">
                        <th class="p-2 text-left">Category Excerpt</th>
                        <th class="p-2 text-left">News Excerpt</th>
                        <th class="p-2 text-left">Reasoning</th>
                    </tr></thead>
                    <tbody>
                        ${insight.reasoning_table.map(r => `
                            <tr class="border-t">
                                <td class="p-2">${r.category_excerpt}</td>
                                <td class="p-2">${r.news_excerpt}</td>
                                <td class="p-2">${r.reasoning}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div class="mt-4 p-3 bg-white border rounded">
                    <h5 class="font-semibold mb-2">Your Feedback (Required)</h5>
                    <div class="flex gap-2 mb-2">
                        <button onclick="submitFeedback('${articleId}', true)" class="px-3 py-1 bg-green-100 rounded">👍</button>
                        <button onclick="submitFeedback('${articleId}', false)" class="px-3 py-1 bg-red-100 rounded">👎</button>
                    </div>
                    <select id="correct-cat-${articleId}" class="w-full border rounded p-2 mb-2">
                        <option value="">Correct Category</option>
                    </select>
                    <textarea id="reasoning-${articleId}" class="w-full border rounded p-2 mb-2" placeholder="Your reasoning"></textarea>
                    <textarea id="note-${articleId}" class="w-full border rounded p-2" placeholder="Additional notes"></textarea>
                </div>
            </div>
        `;
    }

    function submitFeedback(articleId, thumbsUp) {
        const wsId = getWorkspaceId();
        const correctCat = document.getElementById('correct-cat-' + articleId).value;
        const reasoning = document.getElementById('reasoning-' + articleId).value;
        const note = document.getElementById('note-' + articleId).value;

        if (!correctCat || !reasoning || !note) {
            alert('All feedback fields are required');
            return;
        }

        fetch(`/api/workspaces/${wsId}/feedback`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                article_id: articleId,
                thumbs_up: thumbsUp,
                correct_category: correctCat,
                reasoning: reasoning,
                note: note,
                ai_insight: window.currentInsight
            })
        })
        .then(r => r.json())
        .then(report => {
            alert('Evaluation Report: ' + report.summary);
        });
    }

    function suggestImprovements() {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }

        document.getElementById('suggestions-content').innerHTML = 'Loading...';
        document.getElementById('suggestions-modal').classList.remove('hidden');

        fetch(`/api/workspaces/${wsId}/suggest-improvements`, {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            document.getElementById('suggestions-content').innerHTML = `
                <h3 class="font-semibold mt-4">Category Suggestions</h3>
                <ul class="list-disc pl-5">
                    ${data.category_suggestions.map(s => `<li>${s.category}: ${s.rationale}</li>`).join('')}
                </ul>
                <h3 class="font-semibold mt-4">Priority</h3>
                <ol class="list-decimal pl-5">
                    ${data.priority_order.map(p => `<li>${p}</li>`).join('')}
                </ol>
            `;
        })
        .catch(err => {
            document.getElementById('suggestions-content').innerHTML = 'Error: ' + err.message;
        });
    }

    function closeSuggestionsModal() {
        document.getElementById('suggestions-modal').classList.add('hidden');
    }
</script>
{% endblock %}
```

**Step 2: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat: add news list template with HTMX interactions"
```

---

### Task 24: Prompts Editor Template

**Files:**
- Create: `app/templates/prompts.html`

**Step 1: Create prompts editor template**

Create `app/templates/prompts.html`:
```html
{% extends "base.html" %}

{% block title %}Prompts - Prompt Enhancer{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">Prompt Editor</h1>

<div class="bg-white rounded-lg shadow">
    <div class="border-b">
        <nav class="flex">
            <button onclick="showTab('categories')" id="tab-categories"
                    class="px-6 py-3 border-b-2 border-blue-600 text-blue-600">
                Category Definitions
            </button>
            <button onclick="showTab('fewshots')" id="tab-fewshots"
                    class="px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700">
                Few-Shot Examples
            </button>
        </nav>
    </div>

    <div id="panel-categories" class="p-6">
        <div id="categories-list" class="space-y-4 mb-4"></div>
        <button onclick="addCategory()" class="bg-blue-600 text-white px-4 py-2 rounded">+ Add Category</button>
        <button onclick="saveCategories()" class="bg-green-600 text-white px-4 py-2 rounded ml-2">Save</button>
    </div>

    <div id="panel-fewshots" class="p-6 hidden">
        <div id="fewshots-list" class="space-y-4 mb-4"></div>
        <button onclick="addFewShot()" class="bg-blue-600 text-white px-4 py-2 rounded">+ Add Example</button>
        <button onclick="saveFewShots()" class="bg-green-600 text-white px-4 py-2 rounded ml-2">Save</button>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    let categories = [];
    let fewShots = [];

    function showTab(tab) {
        document.getElementById('panel-categories').classList.toggle('hidden', tab !== 'categories');
        document.getElementById('panel-fewshots').classList.toggle('hidden', tab !== 'fewshots');
        document.getElementById('tab-categories').classList.toggle('border-blue-600', tab === 'categories');
        document.getElementById('tab-categories').classList.toggle('text-blue-600', tab === 'categories');
        document.getElementById('tab-fewshots').classList.toggle('border-blue-600', tab === 'fewshots');
        document.getElementById('tab-fewshots').classList.toggle('text-blue-600', tab === 'fewshots');
    }

    function loadPrompts() {
        const wsId = getWorkspaceId();
        if (!wsId) return;

        fetch(`/api/workspaces/${wsId}/prompts/categories`)
            .then(r => r.json())
            .then(data => {
                categories = data.categories;
                renderCategories();
            });

        fetch(`/api/workspaces/${wsId}/prompts/few-shots`)
            .then(r => r.json())
            .then(data => {
                fewShots = data.examples;
                renderFewShots();
            });
    }

    function renderCategories() {
        document.getElementById('categories-list').innerHTML = categories.map((c, i) => `
            <div class="border rounded p-4">
                <input type="text" value="${c.name}" onchange="categories[${i}].name=this.value"
                       class="w-full border rounded p-2 mb-2" placeholder="Category Name">
                <textarea onchange="categories[${i}].definition=this.value"
                          class="w-full border rounded p-2" rows="3" placeholder="Definition">${c.definition}</textarea>
                <button onclick="categories.splice(${i},1);renderCategories()" class="text-red-600 text-sm mt-2">Remove</button>
            </div>
        `).join('');
    }

    function addCategory() {
        categories.push({name: '', definition: ''});
        renderCategories();
    }

    function saveCategories() {
        const wsId = getWorkspaceId();
        fetch(`/api/workspaces/${wsId}/prompts/categories`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({categories})
        }).then(() => alert('Categories saved!'));
    }

    function renderFewShots() {
        document.getElementById('fewshots-list').innerHTML = fewShots.map((f, i) => `
            <div class="border rounded p-4">
                <input type="text" value="${f.id}" readonly class="w-full border rounded p-2 mb-2 bg-gray-100">
                <textarea onchange="fewShots[${i}].news_content=this.value"
                          class="w-full border rounded p-2 mb-2" rows="2" placeholder="News Content">${f.news_content}</textarea>
                <input type="text" value="${f.category}" onchange="fewShots[${i}].category=this.value"
                       class="w-full border rounded p-2 mb-2" placeholder="Category">
                <textarea onchange="fewShots[${i}].reasoning=this.value"
                          class="w-full border rounded p-2" rows="2" placeholder="Reasoning">${f.reasoning}</textarea>
                <button onclick="fewShots.splice(${i},1);renderFewShots()" class="text-red-600 text-sm mt-2">Remove</button>
            </div>
        `).join('');
    }

    function addFewShot() {
        fewShots.push({id: 'ex-' + Date.now(), news_content: '', category: '', reasoning: ''});
        renderFewShots();
    }

    function saveFewShots() {
        const wsId = getWorkspaceId();
        fetch(`/api/workspaces/${wsId}/prompts/few-shots`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({examples: fewShots})
        }).then(() => alert('Few-shots saved!'));
    }

    document.getElementById('workspace-selector').addEventListener('change', loadPrompts);
    if (getWorkspaceId()) loadPrompts();
</script>
{% endblock %}
```

**Step 2: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat: add prompts editor template"
```

---

## Phase 7: Final Setup

### Task 25: Update Route Imports

**Files:**
- Modify: `app/routes/__init__.py`

**Step 1: Update routes init**

Update `app/routes/__init__.py`:
```python
from app.routes import news, pages, prompts, workflows, workspaces

__all__ = ["news", "pages", "prompts", "workflows", "workspaces"]
```

**Step 2: Commit**

```bash
git add app/routes/__init__.py
git commit -m "feat: export all route modules"
```

---

### Task 26: Create Sample News CSV

**Files:**
- Create: `data/sample_news.csv`

**Step 1: Create sample data**

Create `data/sample_news.csv`:
```csv
id,headline,content
news-001,Company X Announces Q3 Earnings Call,"Company X today announced it will hold its Q3 earnings call on October 15th at 2:00 PM EST. Analysts expect revenue of $2.5B."
news-002,Breaking: CEO of TechCorp Resigns Unexpectedly,"In a surprise move, TechCorp CEO John Smith announced his immediate resignation citing personal reasons. The board has appointed CFO Jane Doe as interim CEO."
news-003,Industry Report Shows Steady Growth,"A new industry report released today shows the sector grew 5% year-over-year, in line with analyst expectations."
news-004,Company Y Acquires Startup Z for $500M,"Company Y announced today it has agreed to acquire Startup Z for $500 million in cash and stock. The deal is expected to close in Q1 2025."
news-005,Quarterly Dividend Declared,"The Board of Directors declared a quarterly dividend of $0.50 per share, payable on December 1st to shareholders of record as of November 15th."
```

**Step 2: Commit**

```bash
git add data/sample_news.csv
git commit -m "feat: add sample news data for testing"
```

---

### Task 27: Run All Tests

**Step 1: Run the full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Commit if any fixes needed**

---

### Task 28: Manual Testing

**Step 1: Start the server**

Run: `uv run uvicorn app.main:app --reload`

**Step 2: Test the UI**

1. Open http://localhost:8000
2. Create a new workspace
3. Go to /prompts and add category definitions
4. Return to / and click "Start AI Workflow" on an article
5. Submit feedback
6. Click "Suggest Prompt Improvements"

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```
