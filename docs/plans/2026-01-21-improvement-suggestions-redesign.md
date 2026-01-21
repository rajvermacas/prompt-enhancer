# Improvement Suggestions Redesign

## Problem Statement

The current ImprovementAgent works on its own predefined training biases without properly incorporating user feedback. Specifically:

1. Feedback cards only show article headline, not the full news content
2. Suggested categories and few-shots don't adhere to user feedback and reasoning
3. ImprovementAgent receives only EvaluationReport summaries, missing the actual user reasoning, correct category, and article content

## Design Principles

- **User reasoning is authoritative** - The user's explanation of why the AI was wrong directly drives suggestions
- **Full context** - The agent receives complete article content, user reasoning, and AI predictions
- **Traceability** - Every suggestion references which feedback item(s) it came from
- **Dual views** - Users can view suggestions by type or grouped by source feedback

## Changes

### 1. Data Model Changes

**`app/models/feedback.py`**

Add `article_content` to `FeedbackWithHeadline`:

```python
class FeedbackWithHeadline(BaseModel):
    id: str
    article_id: str
    article_headline: str
    article_content: str  # NEW
    thumbs_up: bool
    correct_category: str
    reasoning: str
    ai_insight: AIInsight
    created_at: datetime
```

Add traceability fields to suggestion models:

```python
class CategorySuggestionItem(BaseModel):
    category: str
    current: str
    suggested: str
    rationale: str
    based_on_feedback_ids: list[str]
    user_reasoning_quotes: list[str]

class FewShotSuggestionItem(BaseModel):
    action: str  # "add" | "modify" | "remove"
    source: str  # "user_article" | "synthetic"
    based_on_feedback_id: str
    details: dict

class ImprovementSuggestion(BaseModel):
    category_suggestions: list[CategorySuggestionItem]
    few_shot_suggestions: list[FewShotSuggestionItem]
    priority_order: list[str]
    updated_categories: list[UpdatedCategory] = Field(default_factory=list)
    updated_few_shots: list[UpdatedFewShot] = Field(default_factory=list)
```

### 2. API Changes

**`app/routes/workflows.py`**

Update `_enrich_feedbacks_with_headlines` to include article content:

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
            content = article.content  # NEW
        except ArticleNotFoundError:
            headline = f"Article {feedback.article_id} (not found)"
            content = ""  # NEW

        enriched.append(
            FeedbackWithHeadline(
                id=feedback.id,
                article_id=feedback.article_id,
                article_headline=headline,
                article_content=content,  # NEW
                thumbs_up=feedback.thumbs_up,
                correct_category=feedback.correct_category,
                reasoning=feedback.reasoning,
                ai_insight=feedback.ai_insight,
                created_at=feedback.created_at,
            )
        )
    return enriched
```

Update `/suggest-improvements` endpoint to pass feedbacks instead of reports:

```python
@router.post("/suggest-improvements", response_model=ImprovementSuggestionResponse)
def suggest_improvements(...):
    # ... existing setup ...

    feedbacks_with_headlines = _enrich_feedbacks_with_headlines(feedbacks, news_service)

    # CHANGED: pass feedbacks, not reports
    suggestions = agent.suggest_improvements(feedbacks_with_headlines, categories, few_shots)

    return ImprovementSuggestionResponse(
        suggestions=suggestions,
        feedbacks=feedbacks_with_headlines,
    )
```

### 3. ImprovementAgent Rewrite

**`app/agents/improvement_agent.py`**

New system prompt:

```python
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
```

New method signature and prompt building:

```python
class ImprovementAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def suggest_improvements(
        self,
        feedbacks: list[FeedbackWithHeadline],  # CHANGED from reports
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
            parts.append(f"**User Verdict:** {'Correct' if fb.thumbs_up else 'Incorrect'}\n")
            if not fb.thumbs_up:
                parts.append(f"**User's Correct Category:** {fb.correct_category}\n")
            parts.append(f"**User's Reasoning (AUTHORITATIVE):** {fb.reasoning}\n")
            parts.append(f"**AI Predicted:** {fb.ai_insight.category} ({fb.ai_insight.confidence:.0%} confidence)\n")
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
```

### 4. UI Changes

**`app/templates/prompts.html`**

#### 4.1 Collapsible Article Content in Feedback Cards

Update `renderSourceFeedbacks` to include collapsible article content:

```javascript
function renderSourceFeedbacks(feedbackList) {
    // ... existing setup ...

    container.innerHTML = feedbackList.map(fb => `
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-100" id="feedback-card-${fb.id}">
            <!-- existing header, correct_category, reasoning, ai_insight -->

            <!-- NEW: Collapsible Article Content -->
            <div class="mt-3 border-t border-gray-200 pt-3">
                <button onclick="toggleFeedbackContent('${fb.id}')"
                        class="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1">
                    <span id="feedback-content-arrow-${fb.id}" class="transition-transform duration-200">&#9654;</span>
                    <span>Article Content</span>
                </button>
                <div id="feedback-content-${fb.id}" class="hidden mt-2 max-h-48 overflow-y-auto
                     bg-white border border-gray-100 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap">
                    ${escapeHtml(fb.article_content)}
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

#### 4.2 Dual View Toggle

Add view toggle buttons above suggestions:

```html
<div id="suggestions-content" class="hidden space-y-6">
    <!-- NEW: View Toggle -->
    <div class="flex gap-2 mb-4">
        <button onclick="setSuggestionView('by-type')" id="view-by-type-btn"
                class="px-3 py-1.5 text-sm font-medium rounded-lg bg-red-600 text-white">
            By Suggestion Type
        </button>
        <button onclick="setSuggestionView('by-feedback')" id="view-by-feedback-btn"
                class="px-3 py-1.5 text-sm font-medium rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200">
            By Feedback Source
        </button>
    </div>

    <!-- By Type View (existing, enhanced) -->
    <div id="suggestions-by-type">
        <!-- Category Suggestions, Priority Order, Updated Categories, Updated Few-Shots -->
    </div>

    <!-- By Feedback View (new) -->
    <div id="suggestions-by-feedback" class="hidden space-y-4">
        <!-- Populated dynamically -->
    </div>
</div>
```

#### 4.3 Enhanced Suggestion Cards with Attribution

Update `renderCategorySuggestions` to show feedback attribution:

```javascript
function renderCategorySuggestions(suggestions, feedbacks) {
    // ... existing setup ...

    container.innerHTML = suggestions.map(s => {
        const feedbackLinks = (s.based_on_feedback_ids || []).map(id => {
            const fb = feedbacks.find(f => f.id === id);
            return fb
                ? `<a href="#feedback-card-${id}" onclick="highlightFeedback('${id}')"
                     class="text-red-600 hover:underline">${escapeHtml(fb.article_headline)}</a>`
                : id;
        }).join(', ');

        const quotes = (s.user_reasoning_quotes || []).map(q =>
            `<div class="text-xs text-gray-500 italic mt-1">"${escapeHtml(q)}"</div>`
        ).join('');

        return `
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <div class="font-medium text-gray-900 mb-1">${escapeHtml(s.category)}</div>
                <div class="text-sm text-gray-600">${escapeHtml(s.rationale)}</div>
                ${feedbackLinks ? `<div class="text-xs text-gray-500 mt-2">Based on: ${feedbackLinks}</div>` : ''}
                ${quotes}
            </div>
        `;
    }).join('');
}
```

#### 4.4 By Feedback View

```javascript
function renderSuggestionsByFeedback(data) {
    const container = document.getElementById('suggestions-by-feedback');
    const feedbacks = data.feedbacks;
    const catSuggestions = data.suggestions.category_suggestions;
    const fewShotSuggestions = data.suggestions.few_shot_suggestions;

    container.innerHTML = feedbacks.map(fb => {
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
    }).filter(Boolean).join('');
}
```

#### 4.5 Helper Functions

```javascript
let currentSuggestionView = 'by-type';

function setSuggestionView(view) {
    currentSuggestionView = view;
    document.getElementById('suggestions-by-type').classList.toggle('hidden', view !== 'by-type');
    document.getElementById('suggestions-by-feedback').classList.toggle('hidden', view !== 'by-feedback');

    document.getElementById('view-by-type-btn').classList.toggle('bg-red-600', view === 'by-type');
    document.getElementById('view-by-type-btn').classList.toggle('text-white', view === 'by-type');
    document.getElementById('view-by-type-btn').classList.toggle('bg-gray-100', view !== 'by-type');
    document.getElementById('view-by-type-btn').classList.toggle('text-gray-700', view !== 'by-type');

    document.getElementById('view-by-feedback-btn').classList.toggle('bg-red-600', view === 'by-feedback');
    document.getElementById('view-by-feedback-btn').classList.toggle('text-white', view === 'by-feedback');
    document.getElementById('view-by-feedback-btn').classList.toggle('bg-gray-100', view !== 'by-feedback');
    document.getElementById('view-by-feedback-btn').classList.toggle('text-gray-700', view !== 'by-feedback');
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

## Files to Modify

1. `app/models/feedback.py` - Add `article_content` field, add typed suggestion models
2. `app/routes/workflows.py` - Update enrichment function and endpoint
3. `app/agents/improvement_agent.py` - Rewrite prompt and parsing logic
4. `app/templates/prompts.html` - UI changes for feedback cards and dual view

## Migration Notes

- No database migration needed (feedback stored as JSON files)
- EvaluationReport remains for backward compatibility but is no longer used by ImprovementAgent
- Existing feedback will work - article content fetched on demand from news service
