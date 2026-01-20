# Suggest Prompt Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add copy-ready, read-only outputs for changed category definitions and few-shot examples to the Suggest Prompt Improvements modal, without persisting updates.

**Architecture:** Extend the ImprovementAgent response schema to include `updated_categories` and `updated_few_shots`, update the agent prompt + parser accordingly, and render two collapsible copy sections in the modal using these new fields. No backend persistence changes.

**Tech Stack:** FastAPI, Pydantic, LangChain, vanilla JS in Jinja templates.

### Task 1: Extend ImprovementAgent parsing tests

**Files:**
- Modify: `tests/test_improvement_agent.py`

**Step 1: Write the failing test for new response fields**

```python
def test_improvement_agent_parses_updated_fields():
    from app.agents.improvement_agent import ImprovementAgent

    agent = ImprovementAgent(llm=MagicMock())
    raw_response = '''{
        "category_suggestions": [],
        "few_shot_suggestions": [],
        "priority_order": [],
        "updated_categories": [{"category": "Cat1", "updated_definition": "New def"}],
        "updated_few_shots": [{"action": "add", "example": {"id": "ex-1", "news_content": "News", "category": "Cat1", "reasoning": "Reason"}}]
    }'''

    result = agent._parse_response(raw_response)

    assert result.updated_categories[0].category == "Cat1"
    assert result.updated_few_shots[0].action == "add"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_improvement_agent.py::test_improvement_agent_parses_updated_fields -v`  
Expected: FAIL due to missing fields/models.

**Step 3: Commit**

```bash
git add tests/test_improvement_agent.py
git commit -m "test: cover improvement agent updated fields"
```

### Task 2: Update response models for new fields

**Files:**
- Modify: `app/models/feedback.py`

**Step 1: Implement models and wire into ImprovementSuggestion**

```python
from pydantic import BaseModel

class UpdatedCategory(BaseModel):
    category: str
    updated_definition: str

class UpdatedFewShotExample(BaseModel):
    id: str
    news_content: str | None = None
    category: str | None = None
    reasoning: str | None = None

class UpdatedFewShot(BaseModel):
    action: str
    example: UpdatedFewShotExample

class ImprovementSuggestion(BaseModel):
    category_suggestions: list[dict]
    few_shot_suggestions: list[dict]
    priority_order: list[str]
    updated_categories: list[UpdatedCategory] = []
    updated_few_shots: list[UpdatedFewShot] = []
```

**Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_improvement_agent.py::test_improvement_agent_parses_updated_fields -v`  
Expected: FAIL until agent parsing is updated (next task).

**Step 3: Commit**

```bash
git add app/models/feedback.py
git commit -m "feat: add improvement updated output models"
```

### Task 3: Update ImprovementAgent prompt and parser

**Files:**
- Modify: `app/agents/improvement_agent.py`

**Step 1: Update system prompt to request new fields**

```python
IMPROVEMENT_SYSTEM_PROMPT = """...
Respond with a JSON object containing:
- category_suggestions: ...
- few_shot_suggestions: ...
- priority_order: ...
- updated_categories: array of {category, updated_definition} for changed items only
- updated_few_shots: array of {action, example} for changed items only
  - example must include id and full fields for add/modify, id only for remove
"""
```

**Step 2: Update parser to populate new fields**

```python
data = json.loads(cleaned.strip())
return ImprovementSuggestion(
    category_suggestions=data.get("category_suggestions", []),
    few_shot_suggestions=data.get("few_shot_suggestions", []),
    priority_order=data.get("priority_order", []),
    updated_categories=data.get("updated_categories", []),
    updated_few_shots=data.get("updated_few_shots", []),
)
```

**Step 3: Run the targeted tests**

Run: `uv run pytest tests/test_improvement_agent.py -v`  
Expected: PASS.

**Step 4: Commit**

```bash
git add app/agents/improvement_agent.py
git commit -m "feat: extend improvement agent output with updated items"
```

### Task 4: Render updated copy sections in the modal

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add collapsible sections + copy buttons**

Add two `<details>` blocks below the existing suggestions in the modal:

```html
<details class="mt-4">
  <summary class="font-semibold cursor-pointer">Updated Categories (changed only)</summary>
  <div class="mt-2">
    <textarea id="updated-categories-text" readonly class="w-full h-40 border rounded p-2"></textarea>
    <button id="copy-updated-categories" onclick="copyText('updated-categories-text')" class="mt-2 bg-blue-600 text-white px-3 py-1 rounded">Copy</button>
  </div>
</details>
```

Repeat for updated few-shots, and add a small list area for removals.

**Step 2: Update JS rendering to populate these sections**

Add helpers to:
- Format updated categories into a text block.
- Format updated few-shots into a text block (add/modify only).
- Display removals as non-copyable lines.
- Disable copy buttons and show "No changes suggested" for empty arrays.

**Step 3: Manual check**

Run the app and verify that:
- Existing suggestions still render.
- Updated sections show changed items only.
- Copy buttons copy the correct text.
- Removals show as non-copyable items.

**Step 4: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat: show copy-ready updated prompt sections"
```

### Task 5: Full test run

**Step 1: Run the full test suite**

Run: `uv run pytest -q`  
Expected: All tests pass (note current baseline failures in config tests should be addressed separately if still present).

**Step 2: Commit (if needed)**

```bash
git add -A
git commit -m "test: verify updated improvement response workflow"
```
