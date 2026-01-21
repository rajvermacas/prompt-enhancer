# System Prompt Tab Feature Design

## Overview

Add a new "System Prompt" tab to the prompt editor UI that allows users to provide custom instructions for the AI analysis. When provided, the LLM will include a "User-Requested Analysis" section in its response.

## Requirements

1. New tab in prompt editor alongside "Category Definitions" and "Few-Shot Examples"
2. Single free-form text area for custom instructions
3. Instructions injected as a labeled section within the existing prompt structure
4. New "User-Requested Analysis" section in AI Insight display (conditional - only when system prompt exists)
5. LLM response uses structured output via Pydantic models

## Design

### 1. UI Changes (System Prompt Tab)

**Location:** `app/templates/prompts.html`

**Tab Structure:**
```
[Category Definitions] [Few-Shot Examples] [System Prompt]
```

**Tab Content:**
- Single `<textarea>` for free-form instructions
- Placeholder text: "Enter additional instructions for the AI analysis (e.g., 'Mention why other categories were not selected')"
- "Save Changes" button (consistent with other tabs)
- Textarea spans full width, 6-8 rows height

**Behavior:**
- Loads existing system prompt on page load (if any)
- Saves via PUT request to new API endpoint
- Shows success/error toast on save (matching existing pattern)

### 2. Data Storage & API

**New File:** `system_prompt.json` in each workspace directory

**File Structure:**
```json
{
  "content": "Mention why other categories were not selected"
}
```

**New API Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/workspaces/{id}/prompts/system-prompt` | Fetch current system prompt |
| PUT | `/api/workspaces/{id}/prompts/system-prompt` | Save system prompt |

**New Pydantic Models (in `app/models/prompts.py`):**
```python
class SystemPromptConfig(BaseModel):
    content: str
```

**Service Layer (`app/services/prompt_service.py`):**
- Add `get_system_prompt(workspace_id: str) -> SystemPromptConfig` method
- Add `save_system_prompt(workspace_id: str, config: SystemPromptConfig) -> None` method
- Follow existing pattern used for categories and few-shots

### 3. LLM Structured Output

**Changes to `app/models/feedback.py`:**

```python
# New model (extends AIInsight concept)
class AIInsightWithUserAnalysis(BaseModel):
    category: str
    reasoning_table: list[ReasoningRow]
    confidence: float
    user_requested_analysis: str | None = None
```

**Changes to `app/agents/analysis_agent.py`:**

1. Update `analyze()` method signature:
```python
def analyze(
    self,
    categories: list[CategoryDefinition],
    few_shots: list[FewShotExample],
    article_content: str,
    custom_system_prompt: str | None = None,  # NEW
) -> AIInsight:
```

2. Use structured output:
```python
# Choose response model based on whether custom instructions exist
if custom_system_prompt:
    response_model = AIInsightWithUserAnalysis
else:
    response_model = AIInsight

# Use structured output
structured_llm = self.llm.with_structured_output(response_model)
response = structured_llm.invoke(messages)

return response  # Already a Pydantic model
```

3. Update `_build_prompt()` to accept and include custom instructions:
```python
def _build_prompt(
    self,
    categories: list[CategoryDefinition],
    few_shots: list[FewShotExample],
    article_content: str,
    custom_system_prompt: str | None = None,  # NEW
) -> str:
```

When `custom_system_prompt` is provided, add after existing instructions:
```
## Additional Instructions
{custom_system_prompt}

Respond to these instructions in the `user_requested_analysis` field.
```

### 4. Workflow Integration

**Location:** `app/routes/workflows.py`

Update the analyze endpoint to:
1. Fetch system prompt from storage (if exists)
2. Pass to `AnalysisAgent.analyze()` as `custom_system_prompt` parameter

### 5. UI Display (AI Insight)

**Location:** `app/templates/news_list.html`

**Display structure when system prompt was provided:**
```
AI Insight
├── Category Badge
├── Confidence Progress Bar
├── Reasoning Table
│   ├── Category Excerpt
│   ├── News Excerpt
│   └── Reasoning
└── User-Requested Analysis   <-- NEW (conditional)
    └── {text block from LLM}
```

**Conditional rendering:**
- Only render "User-Requested Analysis" section when `user_requested_analysis` field is non-null and non-empty
- Section header: "User-Requested Analysis" in bold
- Content displayed as text block (preserving line breaks)
- Styling consistent with existing reasoning table section

## Files to Create/Modify

### New Files
- None (all changes are modifications)

### Modified Files
1. `app/models/prompts.py` - Add `SystemPromptConfig` model
2. `app/models/feedback.py` - Add `AIInsightWithUserAnalysis` model
3. `app/services/prompt_service.py` - Add get/save system prompt methods
4. `app/routes/prompts.py` - Add GET/PUT endpoints for system prompt
5. `app/agents/analysis_agent.py` - Add structured output, custom prompt parameter
6. `app/routes/workflows.py` - Fetch and pass system prompt to agent
7. `app/templates/prompts.html` - Add System Prompt tab
8. `app/templates/news_list.html` - Add User-Requested Analysis section

## Data Flow

```
User writes System Prompt in UI
    ↓
PUT /api/workspaces/{id}/prompts/system-prompt
    ↓
Saved to system_prompt.json
    ↓
User clicks "AI Assisted Analysis" on article
    ↓
POST /api/workspaces/{id}/analyze
    ↓
Workflow loads system_prompt.json
    ↓
AnalysisAgent.analyze() with custom_system_prompt
    ↓
Prompt includes "## Additional Instructions" section
    ↓
LLM returns structured AIInsightWithUserAnalysis
    ↓
Response includes user_requested_analysis field
    ↓
UI renders "User-Requested Analysis" section (if present)
```
