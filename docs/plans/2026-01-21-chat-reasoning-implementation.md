# Chat Reasoning Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable users to chat with the AI about its classification reasoning via real-time SSE streaming, displayed inline below the AI insight section.

**Architecture:** New chat agent receives full context (article, categories, few-shots, insight) and streams responses via SSE. Frontend uses fetch with ReadableStream to display tokens as they arrive.

**Tech Stack:** FastAPI StreamingResponse, LangChain streaming, vanilla JavaScript ReadableStream API

---

## Task 1: Create Chat Data Models

**Files:**
- Create: `app/models/chat.py`
- Test: `tests/test_models_chat.py`

**Step 1: Write the failing test**

Create `tests/test_models_chat.py`:

```python
import pytest
from pydantic import ValidationError


def test_chat_message_valid():
    """ChatMessage accepts user and assistant roles."""
    from app.models.chat import ChatMessage

    user_msg = ChatMessage(role="user", content="Why this category?")
    assert user_msg.role == "user"
    assert user_msg.content == "Why this category?"

    assistant_msg = ChatMessage(role="assistant", content="Because...")
    assert assistant_msg.role == "assistant"


def test_chat_message_invalid_role():
    """ChatMessage rejects invalid roles."""
    from app.models.chat import ChatMessage

    with pytest.raises(ValidationError):
        ChatMessage(role="system", content="test")


def test_chat_reasoning_request_valid():
    """ChatReasoningRequest validates all fields."""
    from app.models.chat import ChatMessage, ChatReasoningRequest
    from app.models.feedback import AIInsight, ReasoningRow

    insight = AIInsight(
        category="Tech",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="tech news",
                news_excerpt="Apple released",
                reasoning="matches tech"
            )
        ],
        confidence=0.9
    )

    request = ChatReasoningRequest(
        article_id="news-001",
        ai_insight=insight,
        message="Why not Business?",
        chat_history=[ChatMessage(role="user", content="Hello")]
    )

    assert request.article_id == "news-001"
    assert request.message == "Why not Business?"
    assert len(request.chat_history) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models_chat.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.chat'"

**Step 3: Write minimal implementation**

Create `app/models/chat.py`:

```python
from typing import Literal

from pydantic import BaseModel

from app.models.feedback import AIInsight


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatReasoningRequest(BaseModel):
    article_id: str
    ai_insight: AIInsight
    message: str
    chat_history: list[ChatMessage]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models_chat.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/chat.py tests/test_models_chat.py
git commit -m "feat(models): add ChatMessage and ChatReasoningRequest models"
```

---

## Task 2: Create Chat Reasoning Agent

**Files:**
- Create: `app/agents/chat_reasoning_agent.py`
- Test: `tests/test_chat_reasoning_agent.py`

**Step 1: Write the failing test**

Create `tests/test_chat_reasoning_agent.py`:

```python
from unittest.mock import MagicMock

import pytest


def test_chat_reasoning_agent_builds_system_message():
    """ChatReasoningAgent includes all context in system message."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.feedback import AIInsight, ReasoningRow
    from app.models.prompts import CategoryDefinition, FewShotExample

    mock_llm = MagicMock()
    agent = ChatReasoningAgent(llm=mock_llm)

    insight = AIInsight(
        category="Tech",
        reasoning_table=[
            ReasoningRow(
                category_excerpt="technology news",
                news_excerpt="Apple released iPhone",
                reasoning="matches tech definition"
            )
        ],
        confidence=0.85
    )

    categories = [
        CategoryDefinition(name="Tech", definition="Technology news"),
        CategoryDefinition(name="Business", definition="Business news"),
    ]

    few_shots = [
        FewShotExample(
            id="ex1",
            news_content="Google announced",
            category="Tech",
            reasoning="Tech company news"
        )
    ]

    article_content = "Apple released the new iPhone today."

    system_msg = agent._build_system_message(
        article_content=article_content,
        categories=categories,
        few_shots=few_shots,
        ai_insight=insight
    )

    assert "Apple released the new iPhone" in system_msg
    assert "Technology news" in system_msg
    assert "Business news" in system_msg
    assert "Google announced" in system_msg
    assert "Tech" in system_msg
    assert "0.85" in system_msg or "85" in system_msg


def test_chat_reasoning_agent_builds_messages_with_history():
    """ChatReasoningAgent includes chat history in messages."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.chat import ChatMessage
    from app.models.feedback import AIInsight

    mock_llm = MagicMock()
    agent = ChatReasoningAgent(llm=mock_llm)

    insight = AIInsight(category="Tech", reasoning_table=[], confidence=0.9)

    chat_history = [
        ChatMessage(role="user", content="Why Tech?"),
        ChatMessage(role="assistant", content="Because it matches."),
    ]

    messages = agent._build_messages(
        system_message="You are helpful.",
        chat_history=chat_history,
        current_message="What about Business?"
    )

    assert len(messages) == 4
    assert messages[0].content == "You are helpful."
    assert messages[1].content == "Why Tech?"
    assert messages[2].content == "Because it matches."
    assert messages[3].content == "What about Business?"


def test_chat_reasoning_agent_stream_yields_tokens():
    """ChatReasoningAgent.stream yields tokens from LLM."""
    from app.agents.chat_reasoning_agent import ChatReasoningAgent
    from app.models.chat import ChatMessage
    from app.models.feedback import AIInsight
    from app.models.prompts import CategoryDefinition

    mock_llm = MagicMock()
    mock_chunks = [
        MagicMock(content="I "),
        MagicMock(content="classified "),
        MagicMock(content="this."),
    ]
    mock_llm.stream.return_value = iter(mock_chunks)

    agent = ChatReasoningAgent(llm=mock_llm)

    insight = AIInsight(category="Tech", reasoning_table=[], confidence=0.9)
    categories = [CategoryDefinition(name="Tech", definition="Tech news")]

    tokens = list(agent.stream(
        article_content="Test article",
        categories=categories,
        few_shots=[],
        ai_insight=insight,
        chat_history=[],
        message="Why?"
    ))

    assert tokens == ["I ", "classified ", "this."]
    mock_llm.stream.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat_reasoning_agent.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.agents.chat_reasoning_agent'"

**Step 3: Write minimal implementation**

Create `app/agents/chat_reasoning_agent.py`:

```python
from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.models.chat import ChatMessage
from app.models.feedback import AIInsight
from app.models.prompts import CategoryDefinition, FewShotExample


class ChatReasoningAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    def stream(
        self,
        article_content: str,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        ai_insight: AIInsight,
        chat_history: list[ChatMessage],
        message: str,
    ) -> Iterator[str]:
        system_message = self._build_system_message(
            article_content=article_content,
            categories=categories,
            few_shots=few_shots,
            ai_insight=ai_insight,
        )

        messages = self._build_messages(
            system_message=system_message,
            chat_history=chat_history,
            current_message=message,
        )

        for chunk in self.llm.stream(messages):
            if chunk.content:
                yield chunk.content

    def _build_system_message(
        self,
        article_content: str,
        categories: list[CategoryDefinition],
        few_shots: list[FewShotExample],
        ai_insight: AIInsight,
    ) -> str:
        parts = [
            "You are an AI assistant explaining your classification reasoning.",
            "You previously analyzed a news article and classified it into a category.",
            "Now the user wants to understand your thought process.",
            "",
            "YOUR ROLE:",
            "- Explain WHY you made the classification decision",
            "- Compare against other categories when asked",
            "- Reference specific excerpts from the article",
            "- Explain how few-shot examples influenced your thinking",
            "- Be honest about uncertainty or close calls",
            "",
            "DO NOT:",
            "- Re-classify the article",
            "- Change your original decision",
            "- Make up information not in the provided context",
            "",
            "## Original Article",
            article_content,
            "",
            "## Category Definitions Available",
        ]

        for cat in categories:
            parts.append(f"### {cat.name}")
            parts.append(f"{cat.definition}")
            parts.append("")

        if few_shots:
            parts.append("## Few-Shot Examples Used")
            for ex in few_shots:
                parts.append(f"- News: {ex.news_content}")
                parts.append(f"  Category: {ex.category}")
                parts.append(f"  Reasoning: {ex.reasoning}")
                parts.append("")

        parts.append("## Your Classification Result")
        parts.append(f"Category: {ai_insight.category}")
        parts.append(f"Confidence: {ai_insight.confidence:.0%}")
        parts.append("")
        parts.append("Reasoning Table:")
        for row in ai_insight.reasoning_table:
            parts.append(f"- Category Excerpt: {row.category_excerpt}")
            parts.append(f"  News Excerpt: {row.news_excerpt}")
            parts.append(f"  Reasoning: {row.reasoning}")

        return "\n".join(parts)

    def _build_messages(
        self,
        system_message: str,
        chat_history: list[ChatMessage],
        current_message: str,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(content=system_message)]

        for msg in chat_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))

        messages.append(HumanMessage(content=current_message))
        return messages
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_chat_reasoning_agent.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/agents/chat_reasoning_agent.py tests/test_chat_reasoning_agent.py
git commit -m "feat(agents): add ChatReasoningAgent with streaming support"
```

---

## Task 3: Add Chat Reasoning API Endpoint

**Files:**
- Modify: `app/routes/workflows.py`
- Test: `tests/test_routes_workflows.py`

**Step 1: Write the failing test**

Add to `tests/test_routes_workflows.py`:

```python
def test_chat_reasoning_streams_response(client, workspace_id):
    """POST /api/workspaces/{id}/chat-reasoning streams SSE tokens."""
    mock_chunks = [
        MagicMock(content="I "),
        MagicMock(content="chose "),
        MagicMock(content="Tech."),
    ]

    with patch("app.routes.workflows.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.stream.return_value = iter(mock_chunks)
        mock_get_llm.return_value = mock_llm

        response = client.post(
            f"/api/workspaces/{workspace_id}/chat-reasoning",
            json={
                "article_id": "news-001",
                "ai_insight": {
                    "category": "Cat1",
                    "reasoning_table": [],
                    "confidence": 0.9,
                },
                "message": "Why this category?",
                "chat_history": [],
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.text
    assert 'data: {"token": "I "}' in content
    assert 'data: {"token": "chose "}' in content
    assert 'data: {"token": "Tech."}' in content
    assert 'data: {"done": true}' in content


def test_chat_reasoning_workspace_not_found(client):
    """POST /api/workspaces/{id}/chat-reasoning returns 404 for missing workspace."""
    response = client.post(
        "/api/workspaces/nonexistent/chat-reasoning",
        json={
            "article_id": "news-001",
            "ai_insight": {
                "category": "Cat1",
                "reasoning_table": [],
                "confidence": 0.9,
            },
            "message": "Why?",
            "chat_history": [],
        },
    )
    assert response.status_code == 404


def test_chat_reasoning_article_not_found(client, workspace_id):
    """POST /api/workspaces/{id}/chat-reasoning returns 404 for missing article."""
    response = client.post(
        f"/api/workspaces/{workspace_id}/chat-reasoning",
        json={
            "article_id": "nonexistent",
            "ai_insight": {
                "category": "Cat1",
                "reasoning_table": [],
                "confidence": 0.9,
            },
            "message": "Why?",
            "chat_history": [],
        },
    )
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_routes_workflows.py::test_chat_reasoning_streams_response -v`
Expected: FAIL with 404 (endpoint doesn't exist)

**Step 3: Write minimal implementation**

Add to `app/routes/workflows.py` (imports at top, endpoint at bottom):

Add imports:
```python
import json
from fastapi.responses import StreamingResponse
from app.agents.chat_reasoning_agent import ChatReasoningAgent
from app.models.chat import ChatReasoningRequest
```

Add endpoint:
```python
@router.post("/chat-reasoning")
def chat_reasoning(
    workspace_id: str,
    request: ChatReasoningRequest,
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

    llm = get_llm(settings)
    agent = ChatReasoningAgent(llm=llm)

    def generate():
        for token in agent.stream(
            article_content=article.content,
            categories=categories,
            few_shots=few_shots,
            ai_insight=request.ai_insight,
            chat_history=request.chat_history,
            message=request.message,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_routes_workflows.py::test_chat_reasoning_streams_response tests/test_routes_workflows.py::test_chat_reasoning_workspace_not_found tests/test_routes_workflows.py::test_chat_reasoning_article_not_found -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/routes/workflows.py tests/test_routes_workflows.py
git commit -m "feat(api): add /chat-reasoning SSE streaming endpoint"
```

---

## Task 4: Add Chat UI Toggle Button and Container

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add chat section HTML to renderInsight function**

Find the closing `</div>` of `feedback-section-${articleId}` div in `renderInsight()` function and add after it:

```javascript
                <div id="chat-section-${articleId}" class="mt-5">
                    <button onclick="toggleChat('${articleId}')"
                            id="chat-toggle-${articleId}"
                            class="w-full bg-gray-100 text-gray-700 px-4 py-2.5 rounded-lg font-medium hover:bg-gray-200 transition-all duration-200 flex items-center justify-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                        Chat about this reasoning
                    </button>
                    <div id="chat-container-${articleId}" class="hidden mt-4 border border-gray-200 rounded-xl overflow-hidden">
                        <div id="chat-messages-${articleId}" class="h-64 overflow-y-auto p-4 bg-white space-y-3">
                            <div class="flex justify-start">
                                <div class="bg-gray-100 text-gray-700 px-4 py-2 rounded-2xl rounded-bl-md max-w-[80%] text-sm">
                                    Ask me anything about why I classified this article as <strong>${insight.category}</strong>. I can explain my reasoning, compare against other categories, or clarify specific excerpts.
                                </div>
                            </div>
                        </div>
                        <div class="border-t border-gray-200 p-3 bg-gray-50 flex gap-2">
                            <input type="text"
                                   id="chat-input-${articleId}"
                                   placeholder="Ask about the reasoning..."
                                   class="flex-1 border border-gray-200 rounded-lg px-4 py-2 text-sm focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none"
                                   onkeypress="if(event.key === 'Enter') sendChatMessage('${articleId}')">
                            <button onclick="sendChatMessage('${articleId}')"
                                    id="chat-send-${articleId}"
                                    class="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
```

**Step 2: Run manual verification**

Start the server and verify the chat button appears below the feedback section.

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): add chat toggle button and container to insight section"
```

---

## Task 5: Add Chat JavaScript Functions

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add JavaScript state and functions**

Add after `window.currentInsight = null;` at top of script block:

```javascript
    // Chat state per article
    window.chatMessages = {};
    window.chatStreaming = {};
    window.chatAbortControllers = {};
```

**Step 2: Add toggleChat function**

Add before the closing `</script>` tag:

```javascript
    function toggleChat(articleId) {
        const container = document.getElementById('chat-container-' + articleId);
        const button = document.getElementById('chat-toggle-' + articleId);

        if (container.classList.contains('hidden')) {
            container.classList.remove('hidden');
            button.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                Close chat
            `;
            if (!window.chatMessages[articleId]) {
                window.chatMessages[articleId] = [];
            }
        } else {
            container.classList.add('hidden');
            button.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
                Chat about this reasoning
            `;
        }
    }
```

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): add chat toggle functionality"
```

---

## Task 6: Implement SSE Streaming Chat Function

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Add sendChatMessage function with SSE streaming**

Add before the closing `</script>` tag:

```javascript
    async function sendChatMessage(articleId) {
        const input = document.getElementById('chat-input-' + articleId);
        const sendBtn = document.getElementById('chat-send-' + articleId);
        const messagesDiv = document.getElementById('chat-messages-' + articleId);
        const message = input.value.trim();

        if (!message || window.chatStreaming[articleId]) return;

        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }

        // Add user message to UI
        messagesDiv.innerHTML += `
            <div class="flex justify-end">
                <div class="bg-red-600 text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[80%] text-sm">
                    ${escapeHtml(message)}
                </div>
            </div>
        `;

        // Store in history
        if (!window.chatMessages[articleId]) {
            window.chatMessages[articleId] = [];
        }
        window.chatMessages[articleId].push({role: 'user', content: message});

        // Clear input and disable send
        input.value = '';
        sendBtn.disabled = true;
        window.chatStreaming[articleId] = true;

        // Add assistant message placeholder
        const assistantMsgId = 'assistant-msg-' + articleId + '-' + Date.now();
        messagesDiv.innerHTML += `
            <div class="flex justify-start">
                <div id="${assistantMsgId}" class="bg-gray-100 text-gray-700 px-4 py-2 rounded-2xl rounded-bl-md max-w-[80%] text-sm">
                    <span class="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse"></span>
                </div>
            </div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Create abort controller
        window.chatAbortControllers[articleId] = new AbortController();

        try {
            const response = await fetch(`/api/workspaces/${wsId}/chat-reasoning`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    article_id: articleId,
                    ai_insight: window.currentInsight,
                    message: message,
                    chat_history: window.chatMessages[articleId].slice(0, -1)
                }),
                signal: window.chatAbortControllers[articleId].signal
            });

            if (!response.ok) {
                throw new Error('Failed to connect');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantContent = '';
            const assistantMsgEl = document.getElementById(assistantMsgId);

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, {stream: true});
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        try {
                            const data = JSON.parse(jsonStr);
                            if (data.token) {
                                assistantContent += data.token;
                                assistantMsgEl.textContent = assistantContent;
                                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                            }
                        } catch (e) {
                            // Skip malformed JSON
                        }
                    }
                }
            }

            // Store assistant response in history
            window.chatMessages[articleId].push({role: 'assistant', content: assistantContent});

        } catch (err) {
            if (err.name === 'AbortError') {
                // User cancelled
            } else {
                const assistantMsgEl = document.getElementById(assistantMsgId);
                assistantMsgEl.textContent = 'Failed to connect. Please try again.';
                assistantMsgEl.classList.add('text-red-600');
            }
        } finally {
            sendBtn.disabled = false;
            window.chatStreaming[articleId] = false;
            delete window.chatAbortControllers[articleId];
        }
    }
```

**Step 2: Run manual verification**

Start the server, run AI workflow on an article, click "Chat about this reasoning", and send a message. Verify:
- User message appears right-aligned in blue
- Assistant message streams in word-by-word
- Send button is disabled during streaming
- Messages scroll into view

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): implement SSE streaming chat with abort support"
```

---

## Task 7: Run Full Test Suite and Final Verification

**Step 1: Run all tests**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Manual end-to-end test**

1. Start server: `uvicorn app.main:app --reload`
2. Select a workspace
3. Click "Start AI Workflow" on an article
4. Wait for AI insight to appear
5. Click "Chat about this reasoning"
6. Type "Why did you choose this category?" and press Enter
7. Verify streaming response appears
8. Ask follow-up: "What about the other categories?"
9. Verify conversation history is maintained

**Step 3: Commit any fixes and final commit**

```bash
git add -A
git commit -m "feat: complete chat reasoning feature implementation"
```

---

## Summary of Files Changed

| File | Type | Description |
|------|------|-------------|
| `app/models/chat.py` | New | ChatMessage, ChatReasoningRequest models |
| `tests/test_models_chat.py` | New | Model validation tests |
| `app/agents/chat_reasoning_agent.py` | New | Streaming chat agent |
| `tests/test_chat_reasoning_agent.py` | New | Agent unit tests |
| `app/routes/workflows.py` | Modified | Added /chat-reasoning SSE endpoint |
| `tests/test_routes_workflows.py` | Modified | Added endpoint tests |
| `app/templates/news_list.html` | Modified | Added chat UI and JavaScript |
