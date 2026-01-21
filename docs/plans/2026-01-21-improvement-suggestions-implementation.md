# Improvement Suggestions Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make ImprovementAgent use user feedback as authoritative input, with full article content and traceability.

**Architecture:** Update data models to include article content and traceability fields. Rewrite ImprovementAgent to receive FeedbackWithHeadline instead of EvaluationReport. Update UI for collapsible content and dual-view display.

**Tech Stack:** Python/Pydantic models, FastAPI routes, Jinja2/JavaScript templates

---

## Task 1: Add article_content to FeedbackWithHeadline Model

**Files:**
- Modify: `app/models/feedback.py:74-82`
- Test: `tests/test_models_feedback.py`

**Step 1: Write the failing test**

Add to `tests/test_models_feedback.py`:

```python
def test_feedback_with_headline_includes_article_content():
    """FeedbackWithHeadline includes article_content field."""
    from datetime import datetime
    from app.models.feedback import AIInsight, FeedbackWithHeadline

    fb = FeedbackWithHeadline(
        id="fb-001",
        article_id="news-001",
        article_headline="Test Headline",
        article_content="Full article content here",
        thumbs_up=True,
        correct_category="Cat1",
        reasoning="Good classification",
        ai_insight=AIInsight(
            category="Cat1",
            reasoning_table=[],
            confidence=0.9,
        ),
        created_at=datetime.now(),
    )

    assert fb.article_content == "Full article content here"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_feedback.py::test_feedback_with_headline_includes_article_content -v`
Expected: FAIL with validation error (missing field)

**Step 3: Add article_content field to model**

In `app/models/feedback.py`, update `FeedbackWithHeadline`:

```python
class FeedbackWithHeadline(BaseModel):
    id: str
    article_id: str
    article_headline: str
    article_content: str
    thumbs_up: bool
    correct_category: str
    reasoning: str
    ai_insight: AIInsight
    created_at: datetime
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_feedback.py::test_feedback_with_headline_includes_article_content -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/feedback.py tests/test_models_feedback.py
git commit -m "feat(models): add article_content to FeedbackWithHeadline"
```

---

## Task 2: Add Typed Suggestion Models

**Files:**
- Modify: `app/models/feedback.py`
- Test: `tests/test_models_feedback.py`

**Step 1: Write the failing tests**

Add to `tests/test_models_feedback.py`:

```python
def test_category_suggestion_item_creation():
    """CategorySuggestionItem holds suggestion with traceability."""
    from app.models.feedback import CategorySuggestionItem

    item = CategorySuggestionItem(
        category="Technology",
        current="Tech news",
        suggested="Technology and software news",
        rationale="More specific definition",
        based_on_feedback_ids=["fb-001", "fb-002"],
        user_reasoning_quotes=["User said: AI articles should be tech"],
    )

    assert item.category == "Technology"
    assert len(item.based_on_feedback_ids) == 2
    assert "User said" in item.user_reasoning_quotes[0]


def test_few_shot_suggestion_item_creation():
    """FewShotSuggestionItem holds suggestion with source type."""
    from app.models.feedback import FewShotSuggestionItem

    item = FewShotSuggestionItem(
        action="add",
        source="user_article",
        based_on_feedback_id="fb-001",
        details={"id": "ex-1", "news_content": "Test", "category": "Cat1", "reasoning": "Why"},
    )

    assert item.action == "add"
    assert item.source == "user_article"
    assert item.based_on_feedback_id == "fb-001"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models_feedback.py::test_category_suggestion_item_creation tests/test_models_feedback.py::test_few_shot_suggestion_item_creation -v`
Expected: FAIL with ImportError

**Step 3: Add new models**

In `app/models/feedback.py`, add before `ImprovementSuggestion`:

```python
class CategorySuggestionItem(BaseModel):
    category: str
    current: str
    suggested: str
    rationale: str
    based_on_feedback_ids: list[str]
    user_reasoning_quotes: list[str]


class FewShotSuggestionItem(BaseModel):
    action: str
    source: str
    based_on_feedback_id: str
    details: dict
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models_feedback.py::test_category_suggestion_item_creation tests/test_models_feedback.py::test_few_shot_suggestion_item_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/feedback.py tests/test_models_feedback.py
git commit -m "feat(models): add CategorySuggestionItem and FewShotSuggestionItem"
```

---

## Task 3: Update _enrich_feedbacks_with_headlines to Include article_content

**Files:**
- Modify: `app/routes/workflows.py:220-244`
- Test: `tests/test_routes_workflows.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_workflows.py`:

```python
def test_feedback_with_headlines_includes_content(client, workspace_id):
    """GET /api/workspaces/{id}/feedback-with-headlines returns article_content."""
    # First submit feedback
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

        client.post(
            f"/api/workspaces/{workspace_id}/feedback",
            json={
                "article_id": "news-001",
                "thumbs_up": False,
                "correct_category": "Cat2",
                "reasoning": "Wrong category",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.8,
                },
            },
        )

    response = client.get(f"/api/workspaces/{workspace_id}/feedback-with-headlines")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["article_content"] == "Content"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes_workflows.py::test_feedback_with_headlines_includes_content -v`
Expected: FAIL with KeyError or missing field

**Step 3: Update enrichment function**

In `app/routes/workflows.py`, update `_enrich_feedbacks_with_headlines`:

```python
def _enrich_feedbacks_with_headlines(
    feedbacks: list[Feedback],
    news_service: NewsService,
) -> list[FeedbackWithHeadline]:
    enriched = []
    for feedback in feedbacks:
        try:
            article = news_service.get_article(feedback.article_id)
            headline = article.headline
            content = article.content
        except ArticleNotFoundError:
            headline = f"Article {feedback.article_id} (not found)"
            content = ""

        enriched.append(
            FeedbackWithHeadline(
                id=feedback.id,
                article_id=feedback.article_id,
                article_headline=headline,
                article_content=content,
                thumbs_up=feedback.thumbs_up,
                correct_category=feedback.correct_category,
                reasoning=feedback.reasoning,
                ai_insight=feedback.ai_insight,
                created_at=feedback.created_at,
            )
        )
    return enriched
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes_workflows.py::test_feedback_with_headlines_includes_content -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workflows.py tests/test_routes_workflows.py
git commit -m "feat(api): include article_content in feedback-with-headlines"
```

---

## Task 4: Rewrite ImprovementAgent._build_prompt

**Files:**
- Modify: `app/agents/improvement_agent.py`
- Test: `tests/test_improvement_agent.py`

**Step 1: Write the failing test**

Replace test in `tests/test_improvement_agent.py`:

```python
def test_improvement_agent_builds_prompt_from_feedbacks():
    """ImprovementAgent builds prompt from feedbacks with full context."""
    from datetime import datetime
    from unittest.mock import MagicMock

    from app.agents.improvement_agent import ImprovementAgent
    from app.models.feedback import AIInsight, FeedbackWithHeadline, ReasoningRow
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    feedbacks = [
        FeedbackWithHeadline(
            id="fb-001",
            article_id="news-001",
            article_headline="Company X Reports Earnings",
            article_content="Full article about Company X earnings report...",
            thumbs_up=False,
            correct_category="Financial News",
            reasoning="This is about earnings, not technology",
            ai_insight=AIInsight(
                category="Technology",
                reasoning_table=[
                    ReasoningRow(
                        category_excerpt="tech companies",
                        news_excerpt="Company X",
                        reasoning="Company X is tech",
                    )
                ],
                confidence=0.75,
            ),
            created_at=datetime.now(),
        ),
    ]
    categories = [CategoryDefinition(name="Technology", definition="Tech news")]

    prompt = agent._build_prompt(feedbacks, categories, [])

    assert "fb-001" in prompt
    assert "Company X Reports Earnings" in prompt
    assert "Full article about Company X earnings report" in prompt
    assert "This is about earnings, not technology" in prompt
    assert "Financial News" in prompt
    assert "AUTHORITATIVE" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_improvement_agent.py::test_improvement_agent_builds_prompt_from_feedbacks -v`
Expected: FAIL (method signature mismatch or missing content)

**Step 3: Update ImprovementAgent**

Replace entire `app/agents/improvement_agent.py`:

```python
import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.models.feedback import FeedbackWithHeadline, ImprovementSuggestion
from app.models.prompts import CategoryDefinition, FewShotExample


IMPROVEMENT_SYSTEM_PROMPT = """You are a prompt optimization expert. Analyze user feedback and suggest improvements to category definitions and few-shot examples.

CRITICAL: User feedback reasoning is AUTHORITATIVE. Your suggestions MUST directly address what the user explained. Do not override or reinterpret user reasoning with your own judgment.

For each suggestion, you MUST:
1. Reference which feedback ID(s) it addresses
2. Quote the specific user reasoning that drives this suggestion
3. Explain how your suggestion fixes the issue the user identified

When a user marks a classification as incorrect (thumbs down):
- Their correct_category IS the correct answer
- Their reasoning explains WHY - use this to improve definitions
- Consider proposing their article as a new few-shot example (source: "user_article")

You may also suggest synthetic few-shot examples (source: "synthetic") when you identify gaps that user articles don't cover.

Respond with a JSON object containing:
- category_suggestions: array of {category, current, suggested, rationale, based_on_feedback_ids, user_reasoning_quotes}
- few_shot_suggestions: array of {action: "add"|"modify"|"remove", source: "user_article"|"synthetic", based_on_feedback_id, details}
- priority_order: array of strings indicating what to fix first
- updated_categories: array of {category, updated_definition} for changed items only
- updated_few_shots: array of {action, source, example} for changed items only

Rules:
- Return ONLY valid JSON (no markdown).
- Every suggestion MUST have based_on_feedback_ids populated
- Every suggestion MUST quote relevant user reasoning
- For "user_article" few-shots, use the actual article content and user's correct category
"""


class ImprovementAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def suggest_improvements(
        self,
        feedbacks: list[FeedbackWithHeadline],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> ImprovementSuggestion:
        prompt = self._build_prompt(feedbacks, categories, few_shots)
        messages = [
            SystemMessage(content=IMPROVEMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_prompt(
        self,
        feedbacks: list[FeedbackWithHeadline],
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
    ) -> str:
        parts = ["## User Feedback (AUTHORITATIVE)\n\n"]

        for fb in feedbacks:
            parts.append(f"### Feedback {fb.id}\n")
            parts.append(f"**Article Headline:** {fb.article_headline}\n")
            parts.append(f"**Article Content:**\n{fb.article_content}\n\n")
            verdict = "Correct" if fb.thumbs_up else "Incorrect"
            parts.append(f"**User Verdict:** {verdict}\n")
            if not fb.thumbs_up:
                parts.append(f"**User's Correct Category:** {fb.correct_category}\n")
            parts.append(f"**User's Reasoning (AUTHORITATIVE):** {fb.reasoning}\n")
            confidence_pct = f"{fb.ai_insight.confidence:.0%}"
            parts.append(f"**AI Predicted:** {fb.ai_insight.category} ({confidence_pct} confidence)\n")
            if fb.ai_insight.reasoning_table:
                parts.append("**AI Reasoning Table:**\n")
                for row in fb.ai_insight.reasoning_table:
                    parts.append(f"  - {row.category_excerpt} | {row.news_excerpt} | {row.reasoning}\n")
            parts.append("\n")

        parts.append("## Current Category Definitions\n")
        for cat in categories:
            parts.append(f"### {cat.name}\n{cat.definition}\n\n")

        if few_shots:
            parts.append("## Current Few-Shot Examples\n")
            for ex in few_shots:
                parts.append(f"### {ex.id}\n")
                parts.append(f"- Category: {ex.category}\n")
                parts.append(f"- Content: {ex.news_content}\n")
                parts.append(f"- Reasoning: {ex.reasoning}\n\n")

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
            updated_categories=data.get("updated_categories", []),
            updated_few_shots=data.get("updated_few_shots", []),
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_improvement_agent.py::test_improvement_agent_builds_prompt_from_feedbacks -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/improvement_agent.py tests/test_improvement_agent.py
git commit -m "feat(agent): rewrite ImprovementAgent to use feedbacks"
```

---

## Task 5: Update Remaining ImprovementAgent Tests

**Files:**
- Test: `tests/test_improvement_agent.py`

**Step 1: Update test for _parse_response**

Update `tests/test_improvement_agent.py` - replace old tests with:

```python
from datetime import datetime
from unittest.mock import MagicMock

import pytest


def test_improvement_agent_builds_prompt_from_feedbacks():
    """ImprovementAgent builds prompt from feedbacks with full context."""
    from app.agents.improvement_agent import ImprovementAgent
    from app.models.feedback import AIInsight, FeedbackWithHeadline, ReasoningRow
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    feedbacks = [
        FeedbackWithHeadline(
            id="fb-001",
            article_id="news-001",
            article_headline="Company X Reports Earnings",
            article_content="Full article about Company X earnings report...",
            thumbs_up=False,
            correct_category="Financial News",
            reasoning="This is about earnings, not technology",
            ai_insight=AIInsight(
                category="Technology",
                reasoning_table=[
                    ReasoningRow(
                        category_excerpt="tech companies",
                        news_excerpt="Company X",
                        reasoning="Company X is tech",
                    )
                ],
                confidence=0.75,
            ),
            created_at=datetime.now(),
        ),
    ]
    categories = [CategoryDefinition(name="Technology", definition="Tech news")]

    prompt = agent._build_prompt(feedbacks, categories, [])

    assert "fb-001" in prompt
    assert "Company X Reports Earnings" in prompt
    assert "Full article about Company X earnings report" in prompt
    assert "This is about earnings, not technology" in prompt
    assert "Financial News" in prompt
    assert "AUTHORITATIVE" in prompt


def test_improvement_agent_parses_response_with_traceability():
    """ImprovementAgent parses response with traceability fields."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [{
            "category": "Technology",
            "current": "Tech news",
            "suggested": "Technology and software news",
            "rationale": "More specific",
            "based_on_feedback_ids": ["fb-001"],
            "user_reasoning_quotes": ["This is about earnings"]
        }],
        "few_shot_suggestions": [{
            "action": "add",
            "source": "user_article",
            "based_on_feedback_id": "fb-001",
            "details": {"id": "ex-1", "news_content": "Test", "category": "Cat1", "reasoning": "Why"}
        }],
        "priority_order": ["Fix Technology definition"],
        "updated_categories": [{"category": "Technology", "updated_definition": "New def"}],
        "updated_few_shots": [{"action": "add", "source": "user_article", "example": {"id": "ex-1", "news_content": "Test", "category": "Cat1", "reasoning": "Why"}}]
    }'''

    result = agent._parse_response(raw_response)

    assert len(result.category_suggestions) == 1
    assert result.category_suggestions[0]["based_on_feedback_ids"] == ["fb-001"]
    assert len(result.few_shot_suggestions) == 1
    assert result.few_shot_suggestions[0]["source"] == "user_article"
    assert result.priority_order[0] == "Fix Technology definition"


def test_improvement_agent_parses_updated_fields():
    """ImprovementAgent parses updated categories and few-shots."""
    from app.agents.improvement_agent import ImprovementAgent

    mock_llm = MagicMock()
    agent = ImprovementAgent(llm=mock_llm)

    raw_response = '''{
        "category_suggestions": [],
        "few_shot_suggestions": [],
        "priority_order": [],
        "updated_categories": [{"category": "Cat1", "updated_definition": "New def"}],
        "updated_few_shots": [{"action": "add", "example": {"id": "ex-1", "news_content": "News", "category": "Cat1", "reasoning": "Reason"}}]
    }'''

    result = agent._parse_response(raw_response)

    assert result.updated_categories[0]["category"] == "Cat1"
    assert result.updated_few_shots[0]["action"] == "add"
```

**Step 2: Run all tests**

Run: `pytest tests/test_improvement_agent.py -v`
Expected: PASS (all tests)

**Step 3: Commit**

```bash
git add tests/test_improvement_agent.py
git commit -m "test(agent): update ImprovementAgent tests for new signature"
```

---

## Task 6: Update /suggest-improvements Endpoint

**Files:**
- Modify: `app/routes/workflows.py:181-217`
- Test: `tests/test_routes_workflows.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_workflows.py`:

```python
def test_suggest_improvements_uses_feedbacks(client, workspace_id):
    """POST /api/workspaces/{id}/suggest-improvements passes feedbacks to agent."""
    # First submit feedback
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

        client.post(
            f"/api/workspaces/{workspace_id}/feedback",
            json={
                "article_id": "news-001",
                "thumbs_up": False,
                "correct_category": "Cat2",
                "reasoning": "Wrong category",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.8,
                },
            },
        )

    # Now test suggest-improvements
    mock_suggestions = {
        "category_suggestions": [{
            "category": "Cat1",
            "current": "Def1",
            "suggested": "Better def",
            "rationale": "User feedback",
            "based_on_feedback_ids": ["fb-001"],
            "user_reasoning_quotes": ["Wrong category"]
        }],
        "few_shot_suggestions": [],
        "priority_order": ["Fix Cat1"],
        "updated_categories": [],
        "updated_few_shots": []
    }

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = json.dumps(mock_suggestions)
        mock_get_llm.return_value = mock_llm

        response = client.post(f"/api/workspaces/{workspace_id}/suggest-improvements")

    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert "feedbacks" in data
    assert data["feedbacks"][0]["article_content"] == "Content"
```

Note: Add `import json` at top of test file.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes_workflows.py::test_suggest_improvements_uses_feedbacks -v`
Expected: FAIL (old code passes reports, not feedbacks)

**Step 3: Update endpoint**

In `app/routes/workflows.py`, update the `/suggest-improvements` endpoint:

```python
@router.post("/suggest-improvements", response_model=ImprovementSuggestionResponse)
def suggest_improvements(
    workspace_id: str,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    news_service: NewsService = Depends(get_news_service),
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
    feedbacks = feedback_service.list_feedback()

    if not feedbacks:
        raise HTTPException(status_code=400, detail="No feedback available")

    feedbacks_with_headlines = _enrich_feedbacks_with_headlines(feedbacks, news_service)

    llm = get_llm(settings)
    agent = ImprovementAgent(llm=llm)
    suggestions = agent.suggest_improvements(feedbacks_with_headlines, categories, few_shots)

    return ImprovementSuggestionResponse(
        suggestions=suggestions,
        feedbacks=feedbacks_with_headlines,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes_workflows.py::test_suggest_improvements_uses_feedbacks -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workflows.py tests/test_routes_workflows.py
git commit -m "feat(api): update suggest-improvements to use feedbacks"
```

---

## Task 7: Add Collapsible Article Content in UI

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Update renderSourceFeedbacks function**

In `app/templates/prompts.html`, replace the `renderSourceFeedbacks` function:

```javascript
function renderSourceFeedbacks(feedbackList) {
    const container = document.getElementById('source-feedbacks');
    const countEl = document.getElementById('feedback-count');

    if (!feedbackList || feedbackList.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No feedback available. Submit feedback on articles in the News section to see it here.</p>';
        countEl.textContent = '0 items';
        return;
    }

    countEl.textContent = `${feedbackList.length} item${feedbackList.length !== 1 ? 's' : ''}`;

    container.innerHTML = feedbackList.map(fb => `
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-100" id="feedback-card-${fb.id}">
            <div class="flex items-start justify-between mb-2">
                <h4 class="font-medium text-gray-900 flex-1">${escapeHtml(fb.article_headline)}</h4>
                <div class="flex items-center gap-2 flex-shrink-0 ml-2">
                    <span class="${fb.thumbs_up ? 'text-green-600' : 'text-red-600'}">
                        ${fb.thumbs_up ? '&#128077;' : '&#128078;'}
                    </span>
                    <button onclick="deleteFeedback('${fb.id}')"
                            class="text-gray-400 hover:text-red-600 transition-colors duration-150"
                            title="Delete feedback">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
            ${!fb.thumbs_up && fb.correct_category ? `
                <div class="text-sm text-gray-600 mb-2">
                    <span class="font-medium">Correct category:</span> ${escapeHtml(fb.correct_category)}
                </div>
            ` : ''}
            <div class="text-sm text-gray-600 mb-2">
                <span class="font-medium">User reasoning:</span> ${escapeHtml(fb.reasoning)}
            </div>
            <div class="text-sm text-gray-500 mb-3">
                <span class="font-medium">AI insight:</span> ${escapeHtml(fb.ai_insight.category)} (${Math.round(fb.ai_insight.confidence * 100)}% confidence)
            </div>
            <div class="border-t border-gray-200 pt-3">
                <button onclick="toggleFeedbackContent('${fb.id}')"
                        class="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1">
                    <span id="feedback-content-arrow-${fb.id}" class="transition-transform duration-200">&#9654;</span>
                    <span>Article Content</span>
                </button>
                <div id="feedback-content-${fb.id}" class="hidden mt-2 max-h-48 overflow-y-auto bg-white border border-gray-100 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap">
                    ${escapeHtml(fb.article_content || '')}
                </div>
            </div>
        </div>
    `).join('');
}

function toggleFeedbackContent(feedbackId) {
    const content = document.getElementById(`feedback-content-${feedbackId}`);
    const arrow = document.getElementById(`feedback-content-arrow-${feedbackId}`);
    content.classList.toggle('hidden');
    arrow.style.transform = content.classList.contains('hidden') ? '' : 'rotate(90deg)';
}
```

**Step 2: Verify manually**

Run: `python -m app.main` (or your start command)
Navigate to Prompts > Improvement Suggestions, verify collapsible content works.

**Step 3: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): add collapsible article content in feedback cards"
```

---

## Task 8: Add Dual View Toggle UI

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Update suggestions-content section**

In `app/templates/prompts.html`, replace the `suggestions-content` div structure:

```html
<div id="suggestions-content" class="hidden space-y-6">
    <!-- View Toggle -->
    <div class="flex gap-2">
        <button onclick="setSuggestionView('by-type')" id="view-by-type-btn"
                class="px-3 py-1.5 text-sm font-medium rounded-lg bg-red-600 text-white transition-colors duration-150">
            By Suggestion Type
        </button>
        <button onclick="setSuggestionView('by-feedback')" id="view-by-feedback-btn"
                class="px-3 py-1.5 text-sm font-medium rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors duration-150">
            By Feedback Source
        </button>
    </div>

    <!-- By Type View -->
    <div id="suggestions-by-type">
        <!-- Category Suggestions -->
        <div class="border border-gray-200 rounded-xl p-5 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Category Suggestions</h3>
            <div id="category-suggestions" class="space-y-3"></div>
        </div>

        <!-- Priority Order -->
        <div class="border border-gray-200 rounded-xl p-5 mb-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Priority Order</h3>
            <ol id="priority-order" class="list-decimal list-inside space-y-2 text-gray-700"></ol>
        </div>

        <!-- Updated Categories (Collapsible) -->
        <div class="border border-gray-200 rounded-xl mb-6">
            <button onclick="toggleSection('updated-categories')" class="w-full flex items-center justify-between p-5 text-left">
                <div class="flex items-center gap-3">
                    <h3 class="text-lg font-semibold text-gray-900">Updated Categories</h3>
                    <span id="updated-categories-count" class="text-sm text-gray-500"></span>
                </div>
                <span id="updated-categories-arrow" class="text-gray-400 transition-transform duration-200">&#9654;</span>
            </button>
            <div id="updated-categories" class="hidden px-5 pb-5">
                <div class="flex justify-end mb-3">
                    <button onclick="copyUpdatedCategories()" class="text-sm text-red-600 hover:text-red-700 font-medium">Copy JSON to clipboard</button>
                </div>
                <div id="updated-categories-content" class="space-y-3"></div>
            </div>
        </div>

        <!-- Updated Few-Shot Examples (Collapsible) -->
        <div class="border border-gray-200 rounded-xl">
            <button onclick="toggleSection('updated-fewshots')" class="w-full flex items-center justify-between p-5 text-left">
                <div class="flex items-center gap-3">
                    <h3 class="text-lg font-semibold text-gray-900">Updated Few-Shot Examples</h3>
                    <span id="updated-fewshots-count" class="text-sm text-gray-500"></span>
                </div>
                <span id="updated-fewshots-arrow" class="text-gray-400 transition-transform duration-200">&#9654;</span>
            </button>
            <div id="updated-fewshots" class="hidden px-5 pb-5">
                <div class="flex justify-end mb-3">
                    <button onclick="copyUpdatedFewShots()" class="text-sm text-red-600 hover:text-red-700 font-medium">Copy JSON to clipboard</button>
                </div>
                <div id="updated-fewshots-content" class="space-y-3"></div>
            </div>
        </div>
    </div>

    <!-- By Feedback View -->
    <div id="suggestions-by-feedback" class="hidden space-y-4"></div>
</div>
```

**Step 2: Add view toggle JavaScript**

Add to the script section:

```javascript
let currentSuggestionView = 'by-type';

function setSuggestionView(view) {
    currentSuggestionView = view;
    document.getElementById('suggestions-by-type').classList.toggle('hidden', view !== 'by-type');
    document.getElementById('suggestions-by-feedback').classList.toggle('hidden', view !== 'by-feedback');

    const typeBtn = document.getElementById('view-by-type-btn');
    const feedbackBtn = document.getElementById('view-by-feedback-btn');

    if (view === 'by-type') {
        typeBtn.className = 'px-3 py-1.5 text-sm font-medium rounded-lg bg-red-600 text-white transition-colors duration-150';
        feedbackBtn.className = 'px-3 py-1.5 text-sm font-medium rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors duration-150';
    } else {
        typeBtn.className = 'px-3 py-1.5 text-sm font-medium rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors duration-150';
        feedbackBtn.className = 'px-3 py-1.5 text-sm font-medium rounded-lg bg-red-600 text-white transition-colors duration-150';
    }
}
```

**Step 3: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): add dual view toggle for suggestions"
```

---

## Task 9: Add Enhanced Category Suggestions with Attribution

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Update renderCategorySuggestions function**

Replace in `app/templates/prompts.html`:

```javascript
function renderCategorySuggestions(suggestions, feedbacks) {
    const container = document.getElementById('category-suggestions');
    if (!suggestions || suggestions.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No category suggestions.</p>';
        return;
    }

    container.innerHTML = suggestions.map(s => {
        const feedbackLinks = (s.based_on_feedback_ids || []).map(id => {
            const fb = feedbacks.find(f => f.id === id);
            return fb
                ? `<a href="#feedback-card-${id}" onclick="highlightFeedback('${id}')" class="text-red-600 hover:underline">${escapeHtml(fb.article_headline)}</a>`
                : id;
        }).join(', ');

        const quotes = (s.user_reasoning_quotes || []).map(q =>
            `<div class="text-xs text-gray-500 italic mt-1">"${escapeHtml(q)}"</div>`
        ).join('');

        return `
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div class="font-medium text-gray-900 mb-1">${escapeHtml(s.category || s.suggestion || 'Suggestion')}</div>
                <div class="text-sm text-gray-600">${escapeHtml(s.rationale || s.description || '')}</div>
                ${feedbackLinks ? `<div class="text-xs text-gray-500 mt-2">Based on: ${feedbackLinks}</div>` : ''}
                ${quotes}
            </div>
        `;
    }).join('');
}

function highlightFeedback(feedbackId) {
    const card = document.getElementById(`feedback-card-${feedbackId}`);
    if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.classList.add('ring-2', 'ring-red-500');
        setTimeout(() => card.classList.remove('ring-2', 'ring-red-500'), 2000);
    }
}
```

**Step 2: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): add feedback attribution to category suggestions"
```

---

## Task 10: Add By Feedback View Rendering

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Add renderSuggestionsByFeedback function**

Add to script section:

```javascript
function renderSuggestionsByFeedback(data) {
    const container = document.getElementById('suggestions-by-feedback');
    const feedbacks = data.feedbacks || [];
    const catSuggestions = data.suggestions.category_suggestions || [];
    const fewShotSuggestions = data.suggestions.few_shot_suggestions || [];

    const cards = feedbacks.map(fb => {
        const relatedCatSuggestions = catSuggestions.filter(s =>
            (s.based_on_feedback_ids || []).includes(fb.id)
        );
        const relatedFewShotSuggestions = fewShotSuggestions.filter(s =>
            s.based_on_feedback_id === fb.id
        );

        if (relatedCatSuggestions.length === 0 && relatedFewShotSuggestions.length === 0) {
            return '';
        }

        return `
            <div class="border border-gray-200 rounded-xl p-5">
                <div class="flex items-center gap-2 mb-3">
                    <span class="${fb.thumbs_up ? 'text-green-600' : 'text-red-600'}">
                        ${fb.thumbs_up ? '&#128077;' : '&#128078;'}
                    </span>
                    <h4 class="font-medium text-gray-900">${escapeHtml(fb.article_headline)}</h4>
                </div>
                <div class="text-sm text-gray-600 mb-3">User said: "${escapeHtml(fb.reasoning)}"</div>

                ${relatedCatSuggestions.length > 0 ? `
                    <div class="mb-3">
                        <div class="text-xs font-medium text-gray-500 uppercase mb-2">Category Suggestions</div>
                        ${relatedCatSuggestions.map(s => `
                            <div class="bg-white border border-gray-100 rounded p-3 mb-2">
                                <div class="font-medium text-sm">${escapeHtml(s.category)}</div>
                                <div class="text-xs text-gray-600">${escapeHtml(s.rationale)}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                ${relatedFewShotSuggestions.length > 0 ? `
                    <div>
                        <div class="text-xs font-medium text-gray-500 uppercase mb-2">Few-Shot Suggestions</div>
                        ${relatedFewShotSuggestions.map(s => `
                            <div class="bg-white border border-gray-100 rounded p-3 mb-2">
                                <span class="text-xs px-2 py-0.5 rounded-full ${s.source === 'user_article' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'}">
                                    ${s.source === 'user_article' ? 'From this article' : 'Synthetic'}
                                </span>
                                <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-800 ml-1">
                                    ${escapeHtml(s.action)}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }).filter(Boolean);

    if (cards.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-sm">No suggestions linked to specific feedback.</p>';
    } else {
        container.innerHTML = cards.join('');
    }
}
```

**Step 2: Update renderSuggestions to call both views**

Update `renderSuggestions` function:

```javascript
function renderSuggestions(data) {
    // Update feedbacks with latest data from suggestions response
    feedbacks = data.feedbacks;
    renderSourceFeedbacks(feedbacks);
    renderCategorySuggestions(data.suggestions.category_suggestions, data.feedbacks);
    renderPriorityOrder(data.suggestions.priority_order);
    renderUpdatedCategories(data.suggestions.updated_categories);
    renderUpdatedFewShots(data.suggestions.updated_few_shots);
    renderSuggestionsByFeedback(data);
}
```

**Step 3: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): add by-feedback view for suggestions"
```

---

## Task 11: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 2: Fix any failures**

If any tests fail, fix them before proceeding.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test failures"
```

---

## Task 12: Manual Integration Test

**Step 1: Start the application**

Run: `python -m app.main` (or your start command)

**Step 2: Test the flow**

1. Navigate to News section
2. Analyze an article
3. Submit feedback with thumbs down and reasoning
4. Navigate to Prompts > Improvement Suggestions
5. Verify feedback card shows with collapsible article content
6. Click "Generate Suggestions"
7. Verify suggestions show feedback attribution
8. Click on feedback link to verify highlighting
9. Toggle between "By Type" and "By Feedback" views

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete improvement suggestions redesign

- Add article_content to FeedbackWithHeadline
- Rewrite ImprovementAgent to use feedbacks (user reasoning authoritative)
- Add traceability fields (based_on_feedback_ids, user_reasoning_quotes)
- Add collapsible article content in feedback cards
- Add dual view toggle (by type / by feedback)
- Add clickable feedback attribution in suggestions"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add article_content to FeedbackWithHeadline | models/feedback.py |
| 2 | Add typed suggestion models | models/feedback.py |
| 3 | Update enrichment function | routes/workflows.py |
| 4 | Rewrite ImprovementAgent._build_prompt | agents/improvement_agent.py |
| 5 | Update ImprovementAgent tests | tests/test_improvement_agent.py |
| 6 | Update /suggest-improvements endpoint | routes/workflows.py |
| 7 | Add collapsible article content UI | templates/prompts.html |
| 8 | Add dual view toggle UI | templates/prompts.html |
| 9 | Add category suggestions attribution | templates/prompts.html |
| 10 | Add by-feedback view rendering | templates/prompts.html |
| 11 | Run full test suite | - |
| 12 | Manual integration test | - |
