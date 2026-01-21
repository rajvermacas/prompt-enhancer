# News Upload Feature Design

## Overview

Add workspace-scoped news upload functionality via a modal interface, supporting both CSV bulk upload and single article entry.

## Current State

- News loaded from CSV file path set via `NEWS_CSV_PATH` environment variable
- `NewsService` reads CSV once at startup and caches articles in memory
- No upload functionality exists
- News is global (not workspace-specific)

## Requirements

1. Users can upload news articles scoped to a workspace
2. Support CSV bulk upload (columns: `id`, `headline`, `content`, `date`)
3. Support single article entry via form
4. Users can choose to merge uploaded news with default or replace entirely
5. Uploaded news persists with workspace (deleted when workspace is deleted)
6. Date stored as string (no format enforcement)

## Data Model

### Updated NewsArticle

```python
class NewsArticle(BaseModel):
    id: str
    headline: str
    content: str
    date: str | None = None  # String, user-provided format
```

### News Source Enum

```python
class NewsSource(str, Enum):
    MERGE = "merge"      # Uploaded + default news together
    REPLACE = "replace"  # Only uploaded news (fallback to default if none)
```

### Updated WorkspaceMetadata

```python
class WorkspaceMetadata(BaseModel):
    id: str
    name: str
    created_at: datetime
    description: str | None = None
    news_source: NewsSource = NewsSource.MERGE  # New field
```

## Storage

```
data/workspaces/{workspace_id}/
├── metadata.json          # Contains news_source preference
├── uploaded_news.csv      # Workspace-specific uploaded news
├── feedback/
└── evaluation_reports/
```

### uploaded_news.csv Format

```csv
id,headline,content,date
uuid-1,Breaking News,Article content here,2026-01-15
uuid-2,Market Update,More content,Jan 20 2026
```

## API Endpoints

### Upload CSV

```
POST /api/workspaces/{workspace_id}/news/upload-csv
Content-Type: multipart/form-data

Request: file (CSV file)
Response: { "count": 10, "message": "10 articles uploaded" }
```

### Add Single Article

```
POST /api/workspaces/{workspace_id}/news
Content-Type: application/json

Request: { "headline": "...", "content": "...", "date": "..." }
Response: { "id": "uuid", "headline": "...", "content": "...", "date": "..." }
```

### Get Workspace News

```
GET /api/workspaces/{workspace_id}/news?page=1&limit=10

Response: {
    "articles": [...],
    "total": 100,
    "page": 1,
    "limit": 10
}
```

Returns news based on workspace's `news_source` preference:
- `merge`: uploaded news + default news
- `replace`: only uploaded news (falls back to default if none uploaded)

### Set News Source

```
PUT /api/workspaces/{workspace_id}/news-source
Content-Type: application/json

Request: { "news_source": "merge" | "replace" }
Response: { "news_source": "merge" }
```

## Service Layer

### WorkspaceNewsService

New service: `app/services/workspace_news_service.py`

```python
class WorkspaceNewsService:
    def upload_csv(self, workspace_id: str, file: UploadFile) -> int:
        """Upload CSV file, append to uploaded_news.csv. Returns count."""

    def add_article(self, workspace_id: str, headline: str, content: str, date: str) -> NewsArticle:
        """Add single article with auto-generated UUID."""

    def get_news(self, workspace_id: str, page: int, limit: int) -> NewsListResponse:
        """Get news respecting workspace's news_source preference."""

    def get_news_source(self, workspace_id: str) -> NewsSource:
        """Get workspace's news source preference."""

    def set_news_source(self, workspace_id: str, source: NewsSource) -> None:
        """Update workspace's news source preference."""
```

## Validation

### CSV Upload

| Check | Error Message |
|-------|---------------|
| Missing columns | "CSV must have columns: id, headline, content, date" |
| Empty file | "CSV file is empty" |
| Duplicate id in file | "Duplicate id 'X' found in CSV" |

No date format validation - stored as-is.

### Single Article

| Field | Validation |
|-------|------------|
| headline | Required, non-empty |
| content | Required, non-empty |
| date | Required, non-empty |
| id | Auto-generated (UUID) |

## UI Design

### Trigger

"Upload News" button in news list header, visible only when workspace is selected.

### Modal Structure

```
┌─────────────────────────────────────────────────────┐
│  Upload News                                    [X] │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐    │
│  │ [CSV Upload]  [Single Article]              │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ─── CSV Upload Tab ───                             │
│  Upload a CSV file with columns:                    │
│  id, headline, content, date                        │
│                                                     │
│  [  Drop CSV file here or click to browse  ]       │
│                                                     │
│  ─── Single Article Tab ───                         │
│  Headline: [________________________]               │
│  Date:     [________________________]               │
│            (e.g., 2026-01-15, Jan 15 2026)         │
│  Content:  [________________________]               │
│            [________________________]               │
│                                                     │
├─────────────────────────────────────────────────────┤
│  News Source: ( ) Merge  ( ) Replace                │
├─────────────────────────────────────────────────────┤
│                          [Cancel]  [Upload/Save]    │
└─────────────────────────────────────────────────────┘
```

### Behavior

- Tab selection persisted in localStorage
- News Source radio updates workspace preference immediately on change
- Success toast notification after upload
- Modal closes on successful upload
- News list refreshes automatically after upload
- "Replace" falls back to default news if no uploaded news exists

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `app/services/workspace_news_service.py` | News upload/retrieval logic |
| `app/routes/workspace_news.py` | API endpoints |

### Modified Files

| File | Changes |
|------|---------|
| `app/models/news.py` | Add `date` field, `NewsSource` enum |
| `app/models/workspace.py` | Add `news_source` field to metadata |
| `app/templates/news_list.html` | Add upload button + modal |
| `app/main.py` | Register new router |

## Implementation Order

1. Update `NewsArticle` model - add `date: str | None` field
2. Add `NewsSource` enum to models
3. Update `WorkspaceMetadata` - add `news_source` field
4. Create `WorkspaceNewsService` with all methods
5. Create API routes in `workspace_news.py`
6. Register router in `main.py`
7. Add upload button to `news_list.html`
8. Build modal UI with tabs
9. Add JavaScript for file upload, form submission, news source toggle
10. Update news list fetching to use workspace-scoped endpoint
11. Add tests for service and routes

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| "Replace" selected but no uploads | Fall back to default news |
| Multiple CSV uploads | Append to existing `uploaded_news.csv` |
| Workspace deleted | `uploaded_news.csv` deleted with workspace |
| No workspace selected | Upload button hidden |
| CSV with extra columns | Ignored, only required columns used |
