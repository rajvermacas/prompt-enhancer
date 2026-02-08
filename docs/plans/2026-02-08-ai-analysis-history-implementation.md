# AI Analysis History Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persist every AI analysis run and show paginated per-user run history on article cards.

**Architecture:** Store runs in SQLite (`auth_db_path`) in a dedicated `analysis_runs` table, keep analyze API response unchanged, and add a paginated history endpoint scoped by user/workspace/article. UI renders latest insight plus expandable previous runs.

**Tech Stack:** FastAPI, Pydantic, SQLite, vanilla JS, pytest.

---

### Task 1: Add failing DB tests for analysis history schema

**Files:**
- Modify: `tests/test_db.py`
- Modify: `app/db.py`

1. Add a test asserting `analysis_runs` table and expected indexes exist after `init_db`.
2. Run targeted test and confirm fail.
3. Implement schema creation in `init_db`.
4. Re-run targeted test and confirm pass.

### Task 2: Add failing service tests and implement analysis history service

**Files:**
- Create: `tests/test_analysis_history_service.py`
- Create: `app/models/analysis_history.py`
- Create: `app/services/analysis_history_service.py`

1. Write tests for save/list behavior: newest-first ordering, pagination, user scope.
2. Run targeted tests and confirm fail.
3. Implement models and service with strict validation.
4. Re-run targeted tests and confirm pass.

### Task 3: Add failing workflow route tests and implement backend integration

**Files:**
- Modify: `tests/test_routes_workflows.py`
- Modify: `app/routes/workflows.py`
- Modify: `app/dependencies.py`

1. Add route tests for:
   - analyze persists run
   - history endpoint returns current user runs only
   - history endpoint pagination
   - workspace authorization checks
2. Run targeted tests and confirm fail.
3. Implement dependency wiring, auth helper, analyze persistence, and history route.
4. Re-run targeted tests and confirm pass.

### Task 4: Add UI history rendering and pagination

**Files:**
- Modify: `app/templates/news_list.html`
- Create: `static/js/news-analysis-history.js`

1. Add history container hook in insight card rendering.
2. Add JS module to fetch and render paginated history with expandable section.
3. Trigger history load after successful analyze.
4. Keep `news_list.html` under 800 lines by moving new logic to external script and trimming non-essential comment lines.

### Task 5: Verification

**Files:**
- Verify: `tests/test_db.py`
- Verify: `tests/test_analysis_history_service.py`
- Verify: `tests/test_routes_workflows.py`

1. Run focused tests for changed areas.
2. Run broader workflow tests if needed.
3. Summarize evidence (passed tests and any limitations).
