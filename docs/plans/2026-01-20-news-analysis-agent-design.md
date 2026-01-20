# News Analysis Agent - Design Document

## Overview

A prompt optimization workbench for compliance teams to classify price-sensitive news articles and iteratively refine the classification prompts through feedback loops.

**Goal:** Produce the best possible prompt for use in a separate production agentic system.

## Core Concepts

### Three Prompt Dimensions

1. **Category Definitions** — User-editable descriptions of each news category (e.g., "Planned Price Sensitive", "Unplanned Price Sensitive", "Not Important"). Persisted per workspace.

2. **Few-Shot Examples** — User-provided historical news articles with their correct category and reasoning. Helps the LLM understand classification expectations. Persisted per workspace.

3. **System Prompt** — Hidden from UI. Defines agent personality, output format (3-column reasoning table), and workflow instructions. Stored in `prompts/system_prompt.txt`.

### Workspaces

Isolated environments for prompt experimentation. Each workspace has its own:
- Category definitions
- Few-shot examples
- Feedback history
- Evaluation reports

The news CSV is shared across all workspaces.

## User Workflows

### Workflow 1: Per-Article Analysis & Feedback

```
1. User sees news list with "Start AI Workflow" buttons
                    ↓
2. User clicks button → Analysis Agent runs
                    ↓
3. AI Insight displayed (category + reasoning table)
                    ↓
4. User provides MANDATORY feedback:
   - Thumbs up/down
   - Correct category (if wrong)
   - Reasoning
   - Note
                    ↓
5. Evaluation Agent analyzes automatically:
   - If negative: finds gaps in prompts/few-shots
   - If positive: identifies what worked
                    ↓
6. Concise report shown inline
                    ↓
7. Feedback + report persisted
               [WORKFLOW ENDS]
```

### Workflow 2: Batch Prompt Improvement

```
1. User clicks "Suggest Prompt Improvements"
                    ↓
2. Improvement Agent loads all evaluation reports + current prompts
                    ↓
3. Analyzes patterns across all feedback
                    ↓
4. Outputs specific suggestions for categories and few-shots
                    ↓
5. User reviews and manually applies changes
```

## Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
├─────────────────────────────────────────────────────────────┤
│  Routes:                                                    │
│  ├── /              → News list page (HTMX + Tailwind)     │
│  ├── /prompts       → Prompt editor page                   │
│  ├── /api/workspaces                                       │
│  ├── /api/news                                             │
│  └── /api/workspaces/{id}/* (prompts, analyze, feedback)   │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                  │
│  ├── WorkspaceService  → CRUD for workspaces               │
│  ├── NewsService       → Read/parse CSV                    │
│  ├── PromptService     → Load/save JSON prompt files       │
│  └── FeedbackService   → Persist feedback & reports        │
├─────────────────────────────────────────────────────────────┤
│  Agents:                                                    │
│  ├── AnalysisAgent     → News classification               │
│  ├── EvaluationAgent   → Feedback diagnosis                │
│  └── ImprovementAgent  → Batch suggestions                 │
├─────────────────────────────────────────────────────────────┤
│  LLM Provider (configured via env):                         │
│  └── OpenRouter | Azure OpenAI | Gemini                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Storage

```
data/
├── news.csv                          (SHARED)
└── workspaces/
    └── {workspace_id}/
        ├── metadata.json
        ├── category_definitions.json
        ├── few_shot_examples.json
        ├── feedback/
        │   └── {feedback_id}.json
        └── evaluation_reports/
            └── {report_id}.json

prompts/
└── system_prompt.txt                 (SHARED, hidden from UI)
```

## API Endpoints

### Workspace Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces` | List all workspaces |
| POST | `/api/workspaces` | Create new workspace (blank slate) |
| DELETE | `/api/workspaces/{id}` | Delete workspace |

### News

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/news?page=1&limit=20` | Paginated news from CSV |

### Prompts (workspace-scoped)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/prompts/categories` | Get category definitions |
| PUT | `/api/workspaces/{id}/prompts/categories` | Save category definitions |
| GET | `/api/workspaces/{id}/prompts/few-shots` | Get few-shot examples |
| PUT | `/api/workspaces/{id}/prompts/few-shots` | Save few-shot examples |

### AI Workflows (workspace-scoped)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workspaces/{id}/analyze` | Run Analysis Agent |
| POST | `/api/workspaces/{id}/feedback` | Submit feedback, triggers Evaluation Agent |
| GET | `/api/workspaces/{id}/feedback` | List all feedback |
| POST | `/api/workspaces/{id}/suggest-improvements` | Run Improvement Agent |

## LLM Agents

### Analysis Agent

**Purpose:** Classify a news article into a category with reasoning.

**Input:**
- System prompt
- Category definitions
- Few-shot examples
- News article content

**Output:**
```json
{
  "category": "Planned Price Sensitive",
  "reasoning_table": [
    {
      "category_excerpt": "verbatim from definition",
      "news_excerpt": "verbatim from article",
      "reasoning": "why this matches"
    }
  ],
  "confidence": 0.85
}
```

### Evaluation Agent

**Purpose:** Diagnose why the AI insight was correct or incorrect.

**Input:**
- AI insight that was generated
- User feedback (thumbs, correct category, reasoning, note)
- Current category definitions
- Current few-shot examples

**Output:**
```json
{
  "diagnosis": "what went right/wrong",
  "prompt_gaps": [
    { "location": "category X definition", "issue": "...", "suggestion": "..." }
  ],
  "few_shot_gaps": [
    { "example_id": "1", "issue": "...", "suggestion": "..." }
  ],
  "summary": "concise report for UI"
}
```

### Improvement Agent

**Purpose:** Aggregate patterns across all feedback and suggest prompt improvements.

**Input:**
- All evaluation reports from workspace
- Current category definitions
- Current few-shot examples

**Output:**
```json
{
  "category_suggestions": [
    { "category": "X", "current": "...", "suggested": "...", "rationale": "..." }
  ],
  "few_shot_suggestions": [
    { "action": "add|modify|remove", "details": "..." }
  ],
  "priority_order": ["fix category X first", "then add few-shot for Y"]
}
```

## UI Pages

### Header (all pages)
- Logo / App Name
- Workspace Selector (dropdown)
- "+ New Workspace" button

### News List (`/`)
- "Suggest Prompt Improvements" button (top right)
- Lazy-loaded list of news articles
- Each row: headline, snippet, "Start AI Workflow" button
- Expandable inline section for AI insight, feedback form, evaluation report

### Prompt Editor (`/prompts`)
- Tab: Category Definitions (editable list, add/save)
- Tab: Few-Shot Examples (editable list with news, category, reasoning)

## Project Structure

```
prompt-enhancer/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── pages.py
│   │   ├── workspaces.py
│   │   ├── news.py
│   │   ├── prompts.py
│   │   └── workflows.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── workspace_service.py
│   │   ├── news_service.py
│   │   ├── prompt_service.py
│   │   └── feedback_service.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── llm_provider.py
│   │   ├── analysis_agent.py
│   │   ├── evaluation_agent.py
│   │   └── improvement_agent.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── workspace.py
│   │   ├── news.py
│   │   ├── prompts.py
│   │   └── feedback.py
│   └── templates/
│       ├── base.html
│       ├── news_list.html
│       ├── news_row.html
│       ├── ai_insight.html
│       ├── evaluation_report.html
│       ├── prompts.html
│       └── suggestions.html
├── static/
│   └── css/
│       └── tailwind.css
├── data/
│   ├── news.csv
│   └── workspaces/
├── prompts/
│   └── system_prompt.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Dependencies

```toml
[project]
name = "prompt-enhancer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "jinja2",
    "python-multipart",
    "langchain",
    "langchain-openai",
    "langchain-google-genai",
    "pydantic",
    "pydantic-settings",
]

[tool.uv]
dev-dependencies = [
    "pytest",
    "pytest-asyncio",
    "httpx",
]
```

## Configuration

Environment variables:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | "openrouter", "azure", or "gemini" |
| `OPENROUTER_API_KEY` | API key for OpenRouter |
| `OPENROUTER_MODEL` | Model name (e.g., "anthropic/claude-3.5-sonnet") |
| `AZURE_OPENAI_API_KEY` | API key for Azure OpenAI |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name |
| `GOOGLE_API_KEY` | API key for Gemini |
| `GEMINI_MODEL` | Model name (e.g., "gemini-1.5-pro") |
| `NEWS_CSV_PATH` | Path to shared news CSV |
| `WORKSPACES_PATH` | Path to workspaces directory |
| `SYSTEM_PROMPT_PATH` | Path to hidden system prompt |

## Out of Scope (MVP)

- User authentication
- Multiple CSV sources
- Real-time news ingestion
- Automatic prompt application (user applies suggestions manually)
- Prompt versioning/history
