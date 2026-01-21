# Improvement Suggestions Redesign

## Overview

Move the "Suggest Prompt Improvements" feature from the News page to the Prompts section, and display the source feedbacks that informed the suggestions.

## Changes

### 1. Prompts Page - Add Third Tab

Add "Improvement Suggestions" as a new third tab in `/app/templates/prompts.html`.

### 2. Improvement Suggestions Tab Layout

- **"Generate Suggestions" button** - Triggers the API call
- **Source Feedback section** - Card view of all feedbacks used:
  - Article headline
  - Thumbs up/down indicator
  - Correct category (if changed)
  - User's reasoning
  - AI's original insight
- **Category Suggestions** - Each with inline feedback references (article headlines only)
- **Priority Order** - Numbered list
- **Updated Categories** - Collapsible with copy-to-clipboard
- **Updated Few-Shot Examples** - Collapsible with copy-to-clipboard

### 3. Backend Changes

Update `/api/workspaces/{workspace_id}/suggest-improvements` to return feedback data alongside suggestions.

### 4. News Page Cleanup

Remove the "Suggest Prompt Improvements" button and modal from `news_list.html`.

## Files to Modify

1. `app/templates/prompts.html` - Add third tab with full UI
2. `app/templates/news_list.html` - Remove button and modal
3. `app/routes/workflows.py` - Update API response to include feedbacks
4. `app/models/feedback.py` - Update response model if needed
