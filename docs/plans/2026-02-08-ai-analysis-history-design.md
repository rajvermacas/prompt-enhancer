# AI Analysis History Design

## Context

Today, clicking `AI Assisted Analysis` shows only the latest result in the article card. The result is not persisted, and the previous result is overwritten on every run.

## Confirmed Requirements

- Save history for every analysis run.
- History visibility must be per triggering user only.
- This rule applies regardless of workspace type, including `organization`.
- UI must show latest result plus an expandable `Previous runs (N)` section.
- History is paginated.
- Sorting is newest first.
- Backend persistence must use SQLite.

## Architecture

### Storage

Use the existing database at `auth_db_path` and add a new table:

- `analysis_runs`
  - `id TEXT PRIMARY KEY`
  - `workspace_id TEXT NOT NULL`
  - `article_id TEXT NOT NULL`
  - `triggered_user_id TEXT NOT NULL`
  - `insight_json TEXT NOT NULL`
  - `created_at TEXT NOT NULL`

Indexes:

- `idx_analysis_runs_lookup` on `(workspace_id, article_id, triggered_user_id, created_at DESC)`
- `idx_analysis_runs_user_recent` on `(triggered_user_id, created_at DESC)`

`insight_json` stores the complete AI insight payload as JSON text, including:

- `category`
- `confidence`
- `reasoning_table` rows (`category_excerpt`, `news_excerpt`, `reasoning`)
- `user_requested_analysis` when present

### APIs

Keep existing analyze contract and add a new history endpoint.

- `POST /api/workspaces/{workspace_id}/analyze`
  - Runs analysis as today
  - Persists one history row per successful run
  - Returns latest analysis payload only

- `GET /api/workspaces/{workspace_id}/analysis-history`
  - Query params: `article_id`, `page`, `limit`
  - `limit` fixed to `10` for this feature
  - Returns paginated list for only the current user

Response shape:

- `items`: history entries with `id`, `created_at`, and parsed insight
- `total`, `page`, `limit`, `has_next`

### Authorization

Enforce workspace access checks for analyze/history routes:

- allow if `workspace.user_id == current_user.id`
- allow if `workspace_id == "organization"`
- otherwise `403`

History query always filters by:

- `workspace_id`
- `article_id`
- `triggered_user_id = current_user.id`

## UI Behavior

On each article card:

1. Run analyze and render latest insight.
2. Fetch history page 1 with limit 10.
3. Show collapsed `Previous runs (N)` section.
4. Expand to view run list newest-first.
5. Click a historical run to render its stored snapshot.
6. Support previous/next paging inside the history section.

## Error Handling

Fail fast for invalid input and invalid stored payloads:

- Missing/invalid query params return `400`.
- Unauthorized workspace access returns `403`.
- Missing workspace/article returns existing `404` behavior.
- Invalid persisted JSON/schema raises explicit server error; no silent fallback.

## Testing

- DB tests for table/index creation.
- Service tests for save, pagination, ordering, and user scoping.
- Route tests for persistence on analyze, per-user history visibility, pagination, and authorization checks.
- UI behavior validation through existing workflow tests plus manual verification for history rendering and paging.
