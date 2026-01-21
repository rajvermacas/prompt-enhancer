# System Prompt Tab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a System Prompt tab to the prompt editor that allows users to provide custom instructions, with responses displayed in a "User-Requested Analysis" section.

**Architecture:** New Pydantic model for system prompt config, service layer methods for persistence, API endpoints for CRUD, LangChain structured output for reliable LLM responses, and conditional UI rendering in templates.

**Tech Stack:** FastAPI, Pydantic, LangChain `with_structured_output()`, Jinja2 templates, vanilla JavaScript.

---

## Task 1: Add SystemPromptConfig Model

**Files:**
- Modify: `app/models/prompts.py:20-21`
- Test: `tests/test_models_prompts.py`

**Step 1: Write the failing test**

Add to `tests/test_models_prompts.py`:

```python
def test_system_prompt_config_creation():
    """SystemPromptConfig stores content string."""
    from app.models.prompts import SystemPromptConfig

    config = SystemPromptConfig(content="Mention why other categories were not selected")

    assert config.content == "Mention why other categories were not selected"


def test_system_prompt_config_empty_content():
    """SystemPromptConfig allows empty content string."""
    from app.models.prompts import SystemPromptConfig

    config = SystemPromptConfig(content="")

    assert config.content == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_prompts.py::test_system_prompt_config_creation -v`
Expected: FAIL with "cannot import name 'SystemPromptConfig'"

**Step 3: Write minimal implementation**

Add to `app/models/prompts.py` after `FewShotConfig`:

```python
class SystemPromptConfig(BaseModel):
    content: str
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/prompts.py tests/test_models_prompts.py
git commit -m "feat: add SystemPromptConfig model for custom user instructions"
```

---

## Task 2: Add PromptService Methods for System Prompt

**Files:**
- Modify: `app/services/prompt_service.py:10-11` (add file path)
- Modify: `app/services/prompt_service.py:27` (add methods after save_few_shots)
- Test: `tests/test_prompt_service.py`

**Step 1: Write the failing tests**

Add to `tests/test_prompt_service.py`:

```python
def test_get_system_prompt_returns_empty_when_file_missing(workspace_dir):
    """PromptService returns empty content when system_prompt.json doesn't exist."""
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = service.get_system_prompt()

    assert config.content == ""


def test_save_system_prompt(workspace_dir):
    """PromptService saves system prompt content."""
    from app.models.prompts import SystemPromptConfig
    from app.services.prompt_service import PromptService

    service = PromptService(workspace_dir)
    config = SystemPromptConfig(content="Explain why other categories were rejected")

    service.save_system_prompt(config)
    loaded = service.get_system_prompt()

    assert loaded.content == "Explain why other categories were rejected"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_service.py::test_get_system_prompt_returns_empty_when_file_missing -v`
Expected: FAIL with "has no attribute 'get_system_prompt'"

**Step 3: Write minimal implementation**

Update `app/services/prompt_service.py`:

```python
import json
from pathlib import Path

from app.models.prompts import FewShotConfig, PromptConfig, SystemPromptConfig


class PromptService:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.categories_file = self.workspace_dir / "category_definitions.json"
        self.few_shots_file = self.workspace_dir / "few_shot_examples.json"
        self.system_prompt_file = self.workspace_dir / "system_prompt.json"

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

    def get_system_prompt(self) -> SystemPromptConfig:
        if not self.system_prompt_file.exists():
            return SystemPromptConfig(content="")
        with open(self.system_prompt_file) as f:
            return SystemPromptConfig.model_validate(json.load(f))

    def save_system_prompt(self, config: SystemPromptConfig) -> None:
        with open(self.system_prompt_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/services/prompt_service.py tests/test_prompt_service.py
git commit -m "feat: add PromptService methods for system prompt persistence"
```

---

## Task 3: Add API Endpoints for System Prompt

**Files:**
- Modify: `app/routes/prompts.py:6` (add import)
- Modify: `app/routes/prompts.py:51` (add endpoints after save_few_shots)
- Test: `tests/test_routes_prompts.py`

**Step 1: Write the failing tests**

Add to `tests/test_routes_prompts.py`:

```python
def test_get_system_prompt_empty(client, workspace_id):
    """GET system-prompt returns empty content initially."""
    response = client.get(f"/api/workspaces/{workspace_id}/prompts/system-prompt")

    assert response.status_code == 200
    assert response.json()["content"] == ""


def test_save_system_prompt(client, workspace_id):
    """PUT system-prompt saves and returns content."""
    payload = {"content": "Mention why other categories were not selected"}

    response = client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Mention why other categories were not selected"


def test_get_system_prompt_after_save(client, workspace_id):
    """GET system-prompt returns saved content."""
    client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json={"content": "Custom instructions here"},
    )

    response = client.get(f"/api/workspaces/{workspace_id}/prompts/system-prompt")

    assert response.status_code == 200
    assert response.json()["content"] == "Custom instructions here"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes_prompts.py::test_get_system_prompt_empty -v`
Expected: FAIL with 404 (endpoint doesn't exist)

**Step 3: Write minimal implementation**

Update `app/routes/prompts.py`:

```python
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_settings, get_workspace_service
from app.models.prompts import FewShotConfig, PromptConfig, SystemPromptConfig
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


@router.get("/system-prompt", response_model=SystemPromptConfig)
def get_system_prompt(service: PromptService = Depends(get_prompt_service)):
    return service.get_system_prompt()


@router.put("/system-prompt", response_model=SystemPromptConfig)
def save_system_prompt(
    config: SystemPromptConfig,
    service: PromptService = Depends(get_prompt_service),
):
    service.save_system_prompt(config)
    return config
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/prompts.py tests/test_routes_prompts.py
git commit -m "feat: add GET/PUT endpoints for system prompt"
```

---

## Task 4: Add AIInsightWithUserAnalysis Model

**Files:**
- Modify: `app/models/feedback.py:15-16` (add after AIInsight)
- Test: `tests/test_models_feedback.py`

**Step 1: Write the failing test**

Add to `tests/test_models_feedback.py`:

```python
def test_ai_insight_with_user_analysis_creation():
    """AIInsightWithUserAnalysis includes optional user_requested_analysis field."""
    from app.models.feedback import AIInsightWithUserAnalysis, ReasoningRow

    insight = AIInsightWithUserAnalysis(
        category="Tech",
        reasoning_table=[
            ReasoningRow(category_excerpt="exc", news_excerpt="news", reasoning="r")
        ],
        confidence=0.9,
        user_requested_analysis="Politics was rejected because...",
    )

    assert insight.category == "Tech"
    assert insight.user_requested_analysis == "Politics was rejected because..."


def test_ai_insight_with_user_analysis_optional_field():
    """AIInsightWithUserAnalysis allows None for user_requested_analysis."""
    from app.models.feedback import AIInsightWithUserAnalysis

    insight = AIInsightWithUserAnalysis(
        category="Tech",
        reasoning_table=[],
        confidence=0.8,
    )

    assert insight.user_requested_analysis is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_feedback.py::test_ai_insight_with_user_analysis_creation -v`
Expected: FAIL with "cannot import name 'AIInsightWithUserAnalysis'"

**Step 3: Write minimal implementation**

Add to `app/models/feedback.py` after `AIInsight` class:

```python
class AIInsightWithUserAnalysis(BaseModel):
    category: str
    reasoning_table: list[ReasoningRow]
    confidence: float
    user_requested_analysis: str | None = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_feedback.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/feedback.py tests/test_models_feedback.py
git commit -m "feat: add AIInsightWithUserAnalysis model with optional user analysis field"
```

---

## Task 5: Update AnalysisAgent to Support Custom System Prompt

**Files:**
- Modify: `app/agents/analysis_agent.py`
- Test: `tests/test_analysis_agent.py`

**Step 1: Write the failing tests**

Add to `tests/test_analysis_agent.py`:

```python
def test_analysis_agent_build_prompt_includes_additional_instructions():
    """AnalysisAgent includes Additional Instructions section when custom_system_prompt provided."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [CategoryDefinition(name="Cat1", definition="Definition 1")]

    prompt = agent._build_prompt(
        categories,
        [],
        "Test article",
        custom_system_prompt="Explain why other categories were not selected",
    )

    assert "## Additional Instructions" in prompt
    assert "Explain why other categories were not selected" in prompt
    assert "user_requested_analysis" in prompt


def test_analysis_agent_build_prompt_no_additional_instructions_when_none():
    """AnalysisAgent omits Additional Instructions section when custom_system_prompt is None."""
    from app.agents.analysis_agent import AnalysisAgent
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = AnalysisAgent(llm=mock_llm, system_prompt="You are an analyst.")

    categories = [CategoryDefinition(name="Cat1", definition="Definition 1")]

    prompt = agent._build_prompt(categories, [], "Test article", custom_system_prompt=None)

    assert "## Additional Instructions" not in prompt
    assert "user_requested_analysis" not in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_analysis_agent.py::test_analysis_agent_build_prompt_includes_additional_instructions -v`
Expected: FAIL (TypeError - unexpected argument 'custom_system_prompt')

**Step 3: Write minimal implementation**

Update `app/agents/analysis_agent.py`:

```python
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import AIInsight, AIInsightWithUserAnalysis, ReasoningRow
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
        custom_system_prompt: str | None = None,
    ) -> AIInsight | AIInsightWithUserAnalysis:
        prompt = self._build_prompt(categories, few_shots, article_content, custom_system_prompt)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        if custom_system_prompt:
            structured_llm = self.llm.with_structured_output(AIInsightWithUserAnalysis)
        else:
            structured_llm = self.llm.with_structured_output(AIInsight)

        insight = structured_llm.invoke(messages)

        allowed_categories = {cat.name for cat in categories}
        if insight.category not in allowed_categories:
            coerced = self._coerce_category_from_excerpt(insight, categories)
            if coerced:
                insight.category = coerced
            else:
                raise ValueError(
                    f"LLM returned category '{insight.category}' not in allowed set"
                )

        return insight

    def _build_prompt(
        self,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        article_content: str,
        custom_system_prompt: str | None = None,
    ) -> str:
        parts = ["## Category Definitions\n"]

        parts.append(
            "CRITICAL: Category names may be arbitrary or misleading. "
            "You MUST classify based ONLY on the definition text, NOT the category name. "
            "Match the news content against each definition and select the category "
            "whose DEFINITION best describes the content.\n\n"
        )

        for cat in categories:
            parts.append(f"### {cat.name}\n")
            parts.append(f"**Definition (use this for classification):** {cat.definition}\n\n")

        allowed = [cat.name for cat in categories]
        parts.append("Allowed category names for output (must match exactly):\n")
        for name in allowed:
            parts.append(f"- {name}\n")

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

        if custom_system_prompt:
            parts.append("- user_requested_analysis: your response to the Additional Instructions below\n")

        parts.append(
            "\nRules:\n"
            "- IGNORE category names when deciding classification - use ONLY the definition text\n"
            "- category MUST be one of the Allowed category names listed above (exact match)\n"
            "- category_excerpt MUST be verbatim from the chosen category definition\n"
            "- If the news is semantically neutral but a category is DEFINED as 'neutral news', "
            "select that category regardless of what the category is named\n"
        )

        if custom_system_prompt:
            parts.append("\n## Additional Instructions\n")
            parts.append(custom_system_prompt)
            parts.append("\n\nRespond to these instructions in the `user_requested_analysis` field.\n")

        return "".join(parts)

    def _coerce_category_from_excerpt(
        self,
        insight: AIInsight | AIInsightWithUserAnalysis,
        categories: list[CategoryDefinition],
    ) -> str | None:
        if not insight.reasoning_table:
            return None

        best_category: str | None = None
        best_score = 0
        tie = False

        for cat in categories:
            definition = cat.definition or ""
            if not definition:
                continue

            score_for_cat = 0
            for row in insight.reasoning_table:
                excerpt = (row.category_excerpt or "").strip()
                if not excerpt:
                    continue
                if excerpt in definition:
                    score_for_cat = max(score_for_cat, len(excerpt))

            if score_for_cat > best_score:
                best_score = score_for_cat
                best_category = cat.name
                tie = False
            elif score_for_cat == best_score and score_for_cat != 0:
                tie = True

        if tie or best_score == 0:
            return None
        return best_category
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_analysis_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/analysis_agent.py tests/test_analysis_agent.py
git commit -m "feat: update AnalysisAgent to support custom system prompt with structured output"
```

---

## Task 6: Update Workflow to Pass System Prompt to Agent

**Files:**
- Modify: `app/routes/workflows.py:67-85` (analyze_article function)
- Test: `tests/test_routes_workflows.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_workflows.py`:

```python
def test_analyze_article_with_system_prompt(client, workspace_id):
    """POST /api/workspaces/{id}/analyze includes user_requested_analysis when system prompt set."""
    # First set a system prompt
    client.put(
        f"/api/workspaces/{workspace_id}/prompts/system-prompt",
        json={"content": "Explain why other categories were not selected"},
    )

    mock_insight = {
        "category": "Cat1",
        "reasoning_table": [],
        "confidence": 0.9,
        "user_requested_analysis": "Other categories were not selected because...",
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        # Mock with_structured_output to return a mock that returns our insight
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = MagicMock(**mock_insight)
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/analyze",
            json={"article_id": "news-001"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "user_requested_analysis" in data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes_workflows.py::test_analyze_article_with_system_prompt -v`
Expected: FAIL (user_requested_analysis not in response)

**Step 3: Write minimal implementation**

Update `app/routes/workflows.py` - modify the `analyze_article` function:

```python
@router.post("/analyze")
def analyze_article(
    workspace_id: str,
    request: AnalyzeRequest,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_news_service: WorkspaceNewsService = Depends(get_workspace_news_service),
):
    settings = get_settings()

    try:
        workspace_service.get_workspace(workspace_id)
    except WorkspaceNotFoundError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        article = workspace_news_service.get_article(workspace_id, request.article_id)
    except ArticleNotFoundError:
        raise HTTPException(status_code=404, detail="Article not found")

    workspace_dir = Path(settings.workspaces_path) / workspace_id
    prompt_service = PromptService(workspace_dir)

    categories = prompt_service.get_categories().categories
    few_shots = prompt_service.get_few_shots().examples
    system_prompt_config = prompt_service.get_system_prompt()
    custom_system_prompt = system_prompt_config.content if system_prompt_config.content else None

    if not categories:
        raise HTTPException(
            status_code=400,
            detail="No categories defined in workspace. Please add at least one category before analyzing articles.",
        )

    with open(settings.system_prompt_path) as f:
        system_prompt = f.read()

    llm = get_llm(settings)
    agent = AnalysisAgent(llm=llm, system_prompt=system_prompt)

    return agent.analyze(categories, few_shots, article.content, custom_system_prompt)
```

Also update the imports at the top and the response model annotation. Remove the `response_model=AIInsight` from the decorator since we now return either `AIInsight` or `AIInsightWithUserAnalysis`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes_workflows.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workflows.py tests/test_routes_workflows.py
git commit -m "feat: pass custom system prompt from workspace to analysis agent"
```

---

## Task 7: Add System Prompt Tab to UI

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Add tab button**

In the `<nav>` element (around line 10-25), add a new tab button after "Few-Shot Examples":

```html
<button onclick="showTab('systemprompt')" id="tab-systemprompt"
        class="px-5 py-3 rounded-t-lg font-medium text-sm border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-all duration-200">
    System Prompt
</button>
```

**Step 2: Add tab panel**

After `panel-fewshots` div (around line 50), add:

```html
<div id="panel-systemprompt" class="p-6 hidden">
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Custom Instructions for AI Analysis</label>
        <textarea id="system-prompt-content"
                  class="w-full border border-gray-200 rounded-lg px-4 py-3 text-gray-700 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150 resize-none"
                  rows="8"
                  placeholder="Enter additional instructions for the AI analysis (e.g., 'Mention why other categories were not selected')"></textarea>
        <p class="text-sm text-gray-500 mt-2">These instructions will be included in the AI analysis prompt. The response will appear in a "User-Requested Analysis" section.</p>
    </div>
    <button onclick="saveSystemPrompt()" class="bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-red-500 active:bg-red-700 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 focus:ring-2 focus:ring-red-600/50 focus:ring-offset-2 focus:outline-none">
        Save Changes
    </button>
</div>
```

**Step 3: Update showTab function**

Update the `showTab` function in the script section to include the new tab:

```javascript
function showTab(tab) {
    document.getElementById('panel-categories').classList.toggle('hidden', tab !== 'categories');
    document.getElementById('panel-fewshots').classList.toggle('hidden', tab !== 'fewshots');
    document.getElementById('panel-suggestions').classList.toggle('hidden', tab !== 'suggestions');
    document.getElementById('panel-systemprompt').classList.toggle('hidden', tab !== 'systemprompt');

    const tabs = ['categories', 'fewshots', 'suggestions', 'systemprompt'];
    tabs.forEach(t => {
        const tabEl = document.getElementById(`tab-${t}`);
        const isActive = t === tab;
        tabEl.classList.toggle('border-red-600', isActive);
        tabEl.classList.toggle('text-red-600', isActive);
        tabEl.classList.toggle('bg-red-50/50', isActive);
        tabEl.classList.toggle('border-transparent', !isActive);
        tabEl.classList.toggle('text-gray-500', !isActive);
        tabEl.classList.toggle('bg-transparent', !isActive);
    });

    if (tab === 'suggestions' && !feedbacksLoaded) {
        loadFeedbacks();
    }
}
```

**Step 4: Add JavaScript functions for loading and saving**

Add these functions in the script section:

```javascript
let systemPromptContent = '';

function loadSystemPrompt() {
    const wsId = getWorkspaceId();
    if (!wsId) return;

    fetch(`/api/workspaces/${wsId}/prompts/system-prompt`)
        .then(r => r.json())
        .then(data => {
            systemPromptContent = data.content || '';
            document.getElementById('system-prompt-content').value = systemPromptContent;
        });
}

function saveSystemPrompt() {
    const wsId = getWorkspaceId();
    if (!wsId) {
        alert('Please select a workspace first');
        return;
    }

    const content = document.getElementById('system-prompt-content').value;

    fetch(`/api/workspaces/${wsId}/prompts/system-prompt`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content})
    })
    .then(r => r.json())
    .then(() => {
        systemPromptContent = content;
        alert('System prompt saved!');
    })
    .catch(err => {
        alert('Error saving system prompt: ' + err.message);
    });
}
```

**Step 5: Update loadPrompts to include system prompt**

Update the `loadPrompts` function to also load the system prompt:

```javascript
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

    loadSystemPrompt();
}
```

**Step 6: Manual verification**

Run the app and verify:
1. New "System Prompt" tab appears
2. Can enter text in the textarea
3. Save button works and shows confirmation
4. Content persists after page reload

**Step 7: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat: add System Prompt tab to prompt editor UI"
```

---

## Task 8: Add User-Requested Analysis Section to AI Insight Display

**Files:**
- Modify: `app/templates/news_list.html` (renderInsight function around line 490-583)

**Step 1: Update renderInsight function**

Update the `renderInsight` function to include the User-Requested Analysis section when present:

```javascript
function renderInsight(articleId, insight) {
    const userAnalysisSection = insight.user_requested_analysis ? `
        <div class="mt-4 p-4 bg-white border border-gray-200 rounded-lg">
            <h5 class="font-semibold text-gray-900 mb-2">User-Requested Analysis</h5>
            <p class="text-gray-700 text-sm whitespace-pre-wrap">${escapeHtml(insight.user_requested_analysis)}</p>
        </div>
    ` : '';

    return `
        <div class="border-l-2 border-red-600 bg-gray-50 rounded-r-xl p-5 transition-all duration-300">
            <div class="flex items-center justify-between mb-4">
                <h4 class="font-semibold text-gray-900">AI Insight</h4>
                <span class="bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm font-medium">${insight.category}</span>
            </div>
            <div class="flex items-center gap-2 mb-4">
                <span class="text-sm text-gray-500">Confidence:</span>
                <div class="flex-1 max-w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-red-600 rounded-full transition-all duration-500" style="width: ${(insight.confidence * 100).toFixed(0)}%"></div>
                </div>
                <span class="text-sm font-medium text-gray-700">${(insight.confidence * 100).toFixed(0)}%</span>
            </div>
            <div class="overflow-x-auto rounded-lg border border-gray-200">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="px-4 py-3 text-left text-gray-700 font-medium">Category Excerpt</th>
                            <th class="px-4 py-3 text-left text-gray-700 font-medium">News Excerpt</th>
                            <th class="px-4 py-3 text-left text-gray-700 font-medium">Reasoning</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${insight.reasoning_table.map(r => `
                            <tr class="hover:bg-gray-50 transition-colors duration-150">
                                <td class="px-4 py-3 text-gray-600">${escapeHtml(r.category_excerpt)}</td>
                                <td class="px-4 py-3 text-gray-600">${escapeHtml(r.news_excerpt)}</td>
                                <td class="px-4 py-3 text-gray-600">${escapeHtml(r.reasoning)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${userAnalysisSection}
            <!-- AI Feedback Submission (hidden for future release) -->
            <div id="feedback-section-${articleId}" class="mt-5 p-5 bg-white border border-gray-200 rounded-xl hidden">
                <!-- ... existing feedback section ... -->
            </div>
            <!-- Chat about reasoning (hidden for future release) -->
            <div id="chat-section-${articleId}" class="mt-5 hidden">
                <!-- ... existing chat section ... -->
            </div>
        </div>
    `;
}
```

**Step 2: Manual verification**

Run the app and verify:
1. Without system prompt: No "User-Requested Analysis" section appears
2. With system prompt: "User-Requested Analysis" section appears after reasoning table
3. Content is properly escaped and line breaks are preserved

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat: display User-Requested Analysis section in AI Insight when present"
```

---

## Task 9: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 2: Fix any failures**

If any tests fail, investigate and fix.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: address test failures from system prompt feature"
```

---

## Task 10: Manual End-to-End Testing

**Step 1: Start the application**

Run: `uvicorn app.main:app --reload`

**Step 2: Test the complete flow**

1. Select a workspace
2. Go to Prompt Editor
3. Click "System Prompt" tab
4. Enter: "Mention why other categories were not selected"
5. Click "Save Changes"
6. Go to News page
7. Click "AI Assisted Analysis" on an article
8. Verify:
   - Analysis completes successfully
   - "User-Requested Analysis" section appears
   - Content explains why other categories were rejected

**Step 3: Test without system prompt**

1. Go back to Prompt Editor
2. Clear the system prompt content
3. Save
4. Analyze another article
5. Verify: No "User-Requested Analysis" section appears

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: complete system prompt tab feature implementation"
```
