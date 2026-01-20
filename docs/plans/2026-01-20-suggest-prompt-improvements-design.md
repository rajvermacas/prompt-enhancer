# Suggest Prompt Improvements - Design Document

## Overview

The "Suggest Prompt Improvements" workflow should continue showing guidance (category suggestions and priority order), but also provide copy-ready, read-only outputs for the user to apply manually. Specifically, the modal should include two new sections that list only the changed category definitions and only the changed few-shot examples. These additions must not mutate any backend prompt data. The UI should remain a review-and-copy surface, with the ImprovementAgent producing updated text snippets that the user can paste into the prompt editor.

The key requirements are:
- Keep existing suggestion lists and priority order.
- Add two read-only, collapsible sections for copyable output.
- Show only changed items (not full lists).
- Do not persist any changes automatically.

## API + Agent Output Changes

The ImprovementAgent response will expand to include two new fields alongside the existing suggestion fields:

```json
{
  "category_suggestions": [],
  "few_shot_suggestions": [],
  "priority_order": [],
  "updated_categories": [
    { "category": "Planned Price Sensitive", "updated_definition": "..." }
  ],
  "updated_few_shots": [
    { "action": "add", "example": { "id": "ex-123", "news_content": "...", "category": "...", "reasoning": "..." } },
    { "action": "modify", "example": { "id": "ex-456", "news_content": "...", "category": "...", "reasoning": "..." } },
    { "action": "remove", "example": { "id": "ex-789" } }
  ]
}
```

The prompt instructions for ImprovementAgent will explicitly request these new fields and emphasize that only changed items should be returned. For updated categories, provide full updated definitions. For few-shot examples, provide full content for added or modified examples, and only the id for removals. The existing suggestion arrays remain unchanged and continue to describe rationale and priority. The backend will not persist updates; the new fields are purely for display and copy.

Parsing should be tolerant: if a model omits new fields, default to empty arrays to preserve backward compatibility. Errors in the response should continue to surface in the modal as before, without blocking rendering of the existing suggestion list.

## UI Behavior, Data Flow, and Error Handling

The "Suggest Prompt Improvements" modal will keep the current sections for category suggestions and priority order. Below them, add two collapsible panels: "Updated Categories (changed only)" and "Updated Few-Shot Examples (changed only)." Each panel will render a read-only block and a "Copy" button. Formatting should be copy-friendly and align with how prompts are authored:

- Updated categories block: a "Category Definitions" heading followed by `### <Category>` and the updated definition text for each changed category.
- Updated few-shots block: an "Examples" heading followed by repeated entries with `**News**`, `**Category**`, and `**Reasoning**`.

Removals should be displayed as non-copyable lines (for example, "Remove example: ex-789") so users understand the action without implying there is copyable content. If either list is empty, render "No changes suggested" and disable the copy button.

Data flow remains a single POST to `/api/workspaces/{id}/suggest-improvements`. The response is used to populate existing suggestion lists plus the two new sections. The UI should default missing fields to empty arrays, and the modal should never crash due to missing or malformed new fields.

## Testing and Rollout

Back-end testing should verify the new response fields are parsed and returned. If tests exist around ImprovementAgent parsing, extend them to include `updated_categories` and `updated_few_shots`. If not, add a small test that stubs the LLM response JSON and checks the response model contains the new fields with defaults when missing.

Front-end testing can be manual: open the news list, click "Suggest Prompt Improvements," confirm that existing suggestions remain, and confirm the new sections show changed items only. Verify that the copy buttons copy the formatted output, removals display clearly without copyable content, and empty results show the "No changes suggested" state with disabled copy. This change is low risk because it does not modify prompt data or change existing workflow endpoints; it adds optional output fields and UI elements while preserving the current behavior.
