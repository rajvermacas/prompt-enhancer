# Few-Shot News Content and Priority Order Fix

**Date:** 2026-01-21
**Status:** Ready for implementation

## Problem

1. **Updated Few-Shot Examples** show `news_content: null` for "add" and "modify" actions - users cannot see what news content the example contains
2. **Priority Order** repeats the same text as category/few-shot suggestions instead of providing actionable, impact-based ranking

## Solution

### 1. Fix `news_content` in Updated Few-Shot Examples

**Approach:**
- For `source: "user_article"` → Pull article content from the linked feedback
- For `source: "synthetic"` → LLM generates the news content

**Changes:**

**A. Update `UpdatedFewShot` model** (`app/models/feedback.py`)
- Add `based_on_feedback_id: str | None = None` field

**B. Update LLM system prompt** (`app/agents/improvement_agent.py`)
- Instruct LLM to include `based_on_feedback_id` in `updated_few_shots` for `user_article` source
- Instruct LLM to generate `news_content` for `synthetic` source

**C. Update `ImprovementAgent`** (`app/agents/improvement_agent.py`)
- Modify `_parse_response` to accept feedbacks parameter
- After parsing, for `user_article` examples: look up feedback by `based_on_feedback_id` and populate `example.news_content` from `feedback.article_content`

### 2. Fix Priority Order to be Impact-Based

**Approach:**
- Update LLM prompt to request impact-based ranking
- Format: `"High impact: <description> (affects N feedbacks)"`

**Changes:**

**A. Update LLM system prompt** (`app/agents/improvement_agent.py`)
- Replace vague `priority_order` instruction with explicit impact-based format
- Example: `["High impact: Fix 'Positive news' definition confusion (affects 3 feedbacks)", "Medium impact: Add example for earnings edge case (affects 1 feedback)"]`

## Files to Modify

1. `app/models/feedback.py` - Add `based_on_feedback_id` to `UpdatedFewShot`
2. `app/agents/improvement_agent.py` - Update prompt and parsing logic

## No UI Changes Required

The template already conditionally renders `news_content` when present (lines 667-672 in `prompts.html`).
