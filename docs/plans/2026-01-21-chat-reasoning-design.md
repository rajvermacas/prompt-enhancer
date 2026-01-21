# AI Insight Chat Feature Design

## Overview

Enable users to have a real-time streaming conversation with the AI to understand its classification reasoning. The chat appears inline below the AI insight section, maintaining context with the specific article being discussed.

## User Experience

### Entry Point
- New "Chat about this reasoning" button below the feedback section in the AI insight card
- Clicking expands an inline chat container below the reasoning table

### Chat Interface
- Messages area (scrollable) with:
  - System welcome message: "Ask me anything about why I classified this article as [Category]. I can explain my reasoning, compare against other categories, or clarify specific excerpts."
  - User messages: right-aligned, blue background
  - AI messages: left-aligned, gray background (streams word-by-word)
- Input area with text field and Send button
- Send button disabled while AI is streaming
- Close button to collapse the chat section

### Example User Questions
- "Why didn't you classify this as [other category]?"
- "What made you confident about the news excerpt you chose?"
- "How did the few-shot examples influence your decision?"

### Data Persistence
- Ephemeral: chat history kept in memory only, cleared on page refresh

## Frontend Architecture

### UI Structure (news_list.html)
```
AI Insight Section (existing)
├── Category Badge + Confidence Bar (existing)
├── Reasoning Table (existing)
├── Feedback Section (existing)
└── NEW: Chat Section
    ├── "Chat about this reasoning" toggle button
    └── Chat Container (hidden by default)
        ├── Messages Area (scrollable)
        ├── Input Area (text input + send button)
        └── Close button
```

### JavaScript State
- `chatMessages[articleId]` - Array of `{role: 'user'|'assistant', content: string}`
- `isStreaming[articleId]` - Boolean to disable input during response
- `abortController[articleId]` - For cancelling in-flight requests

### Styling
- Consistent with existing card/insight styling
- Chat bubbles with distinct colors for user vs AI
- Smooth expand/collapse animation

## Backend Architecture

### New API Endpoint

```
POST /api/workspaces/{workspace_id}/chat-reasoning
Content-Type: application/json
Accept: text/event-stream

Request Body:
{
  "article_id": string,
  "ai_insight": { category, reasoning_table, confidence },
  "message": string,
  "chat_history": [ {role, content}, ... ]
}

Response: SSE stream
data: {"token": "I"}
data: {"token": " classified"}
...
data: {"done": true}
```

### New Files

1. **`app/models/chat.py`** - Data models
2. **`app/agents/chat_reasoning_agent.py`** - Chat agent with streaming
3. **`app/routes/workflows.py`** - Add endpoint (existing file)
4. **`app/templates/news_list.html`** - Add chat UI (existing file)

## Data Models

### app/models/chat.py

```python
from pydantic import BaseModel
from typing import Literal
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

## Chat Agent

### System Prompt

```
You are an AI assistant explaining your classification reasoning. You previously
analyzed a news article and classified it into a category. Now the user wants
to understand your thought process.

CONTEXT PROVIDED:
- The original news article you analyzed
- The category definitions you had available
- The few-shot examples that guided your decision
- Your classification result (category, confidence, reasoning table)

YOUR ROLE:
- Explain WHY you made the classification decision
- Compare against other categories when asked
- Reference specific excerpts from the article
- Explain how few-shot examples influenced your thinking
- Be honest about uncertainty or close calls

DO NOT:
- Re-classify the article
- Change your original decision
- Make up information not in the provided context
```

### Context Assembly
The agent receives:
1. Original article content (fetched via article_id)
2. All category definitions for the workspace
3. All few-shot examples for the workspace
4. The AI insight produced during classification
5. Chat history for multi-turn conversation

### Streaming Implementation
- Uses LangChain's `llm.stream()` method
- Each token yielded as SSE event
- Frontend accumulates tokens into message bubble

## SSE Streaming

### Backend (FastAPI)

```python
from fastapi.responses import StreamingResponse

@router.post("/chat-reasoning")
async def chat_reasoning(...):
    async def generate():
        async for token in chat_agent.stream(...):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

### Frontend (JavaScript)

```javascript
async function sendChatMessage(articleId, message) {
    const response = await fetch(`/api/workspaces/${wsId}/chat-reasoning`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ article_id, ai_insight, message, chat_history })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        // Parse SSE format, extract tokens, append to UI
    }
}
```

## Error Handling

- Connection errors: Show "Failed to connect. Try again." message
- Timeout: 60 second limit with graceful message
- User cancellation: Abort fetch, display partial response
- Invalid article_id: Return 404
- Missing context: Return 400 with specific error

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `app/models/chat.py` | New | ChatMessage, ChatReasoningRequest models |
| `app/agents/chat_reasoning_agent.py` | New | Streaming chat agent |
| `app/routes/workflows.py` | Modify | Add /chat-reasoning endpoint |
| `app/templates/news_list.html` | Modify | Add chat UI and JavaScript |
