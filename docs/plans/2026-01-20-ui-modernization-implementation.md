# UI Modernization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the existing Tailwind UI into a fluid, modern interface with smooth animations, sticky blur header, and refined visual polish while maintaining the red/black color theme.

**Architecture:** Server-rendered Jinja2 templates with Tailwind CSS utilities. All changes are CSS class updates and minimal JavaScript additions for scroll detection and animation states. No framework changes needed.

**Tech Stack:** Tailwind CSS (CDN), Vanilla JavaScript, Jinja2 templates

---

## Task 1: Update Base Template - Header & Global Styles

**Files:**
- Modify: `app/templates/base.html`

**Step 1: Add Tailwind config for custom transitions**

Replace line 7:
```html
<script src="https://cdn.tailwindcss.com"></script>
```

With:
```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        theme: {
            extend: {
                transitionDuration: {
                    '150': '150ms',
                    '200': '200ms',
                    '300': '300ms',
                }
            }
        }
    }
</script>
<style type="text/tailwindcss">
    @layer utilities {
        .transition-base {
            @apply transition-all duration-200 ease-out;
        }
        .transition-fast {
            @apply transition-all duration-150 ease-out;
        }
        .transition-slow {
            @apply transition-all duration-300 ease-out;
        }
    }
</style>
```

**Step 2: Update header with sticky blur effect**

Replace lines 11-32 (the entire header block):
```html
<header id="main-header" class="sticky top-0 z-50 bg-black/90 backdrop-blur-md border-b border-white/10 transition-shadow duration-200">
    <div class="max-w-6xl mx-auto px-8 py-4 flex justify-between items-center">
        <a href="/" class="text-xl font-semibold text-white hover:text-gray-200 transition-colors duration-200">Prompt Enhancer</a>
        <nav class="flex items-center gap-6">
            <a href="/" class="nav-link text-gray-400 hover:text-white transition-all duration-200 hover:-translate-y-0.5 {{ 'text-white border-b-2 border-red-600 pb-1' if request.path == '/' else '' }}">News</a>
            <a href="/prompts" class="nav-link text-gray-400 hover:text-white transition-all duration-200 hover:-translate-y-0.5 {{ 'text-white border-b-2 border-red-600 pb-1' if request.path == '/prompts' else '' }}">Prompts</a>
            <div class="flex items-center gap-3">
                <select id="workspace-selector"
                        class="bg-white/10 text-white rounded-lg px-4 py-2 text-sm border-0 cursor-pointer hover:bg-white/20 transition-colors duration-200 focus:ring-2 focus:ring-red-600/50 focus:outline-none">
                    <option value="" class="bg-gray-900">Select Workspace</option>
                    {% for ws in workspaces %}
                    <option value="{{ ws.id }}" class="bg-gray-900">{{ ws.name }}</option>
                    {% endfor %}
                </select>
                <button onclick="createWorkspace()"
                        class="border border-red-600 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-600 hover:text-white transition-all duration-200">
                    + New
                </button>
            </div>
        </nav>
    </div>
</header>
```

**Step 3: Update main container**

Replace line 33:
```html
<main class="max-w-7xl mx-auto px-4 py-6">
```

With:
```html
<main class="max-w-6xl mx-auto px-8 py-8">
```

**Step 4: Update loader template**

Replace lines 36-41:
```html
<template id="loader-template">
    <div class="loader flex flex-col items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-4 border-red-600 border-t-transparent"></div>
        <p class="mt-3 text-gray-600 text-sm loader-text"></p>
    </div>
</template>
```

With:
```html
<template id="loader-template">
    <div class="loader flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-6 w-6 border-2 border-red-600 border-t-transparent"></div>
        <p class="mt-4 text-gray-500 text-sm loader-text"></p>
    </div>
</template>
```

**Step 5: Add scroll detection JavaScript**

Add before the closing `</script>` tag (before line 104):
```javascript

// Header shadow on scroll
const header = document.getElementById('main-header');
let lastScrollY = 0;

function updateHeaderShadow() {
    if (window.scrollY > 10) {
        header.classList.add('shadow-lg');
    } else {
        header.classList.remove('shadow-lg');
    }
    lastScrollY = window.scrollY;
}

window.addEventListener('scroll', updateHeaderShadow, { passive: true });
updateHeaderShadow();
```

**Step 6: Update createLoaderHtml function**

Replace the createLoaderHtml function (lines 51-58):
```javascript
function createLoaderHtml(text) {
    return `
        <div class="loader flex flex-col items-center justify-center py-12">
            <div class="animate-spin rounded-full h-6 w-6 border-2 border-red-600 border-t-transparent"></div>
            <p class="mt-4 text-gray-500 text-sm">${text}</p>
        </div>
    `;
}
```

**Step 7: Commit**

```bash
git add app/templates/base.html
git commit -m "feat(ui): add sticky blur header and global transition utilities"
```

---

## Task 2: Update News List - Header Section & Modal

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Update page header section**

Replace lines 6-12:
```html
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-black">News Articles</h1>
    <button onclick="suggestImprovements()"
            class="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800">
        Suggest Prompt Improvements
    </button>
</div>
```

With:
```html
<div class="flex justify-between items-center mb-8">
    <h1 class="text-2xl font-semibold text-gray-900">News Articles</h1>
    <button onclick="suggestImprovements()"
            class="bg-gray-100 text-gray-700 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-200 active:bg-gray-300 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0">
        Suggest Prompt Improvements
    </button>
</div>
```

**Step 2: Update news list container**

Replace line 14:
```html
<div id="news-list" class="space-y-4">
```

With:
```html
<div id="news-list" class="space-y-5">
```

**Step 3: Update suggestions modal**

Replace lines 18-24:
```html
<div id="suggestions-modal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto border-t-4 border-red-600">
        <h2 class="text-xl font-bold mb-4 text-black">Prompt Improvement Suggestions</h2>
        <div id="suggestions-content"></div>
        <button onclick="closeSuggestionsModal()" class="mt-4 bg-gray-800 text-white px-4 py-2 rounded hover:bg-black">Close</button>
    </div>
</div>
```

With:
```html
<div id="suggestions-modal" class="hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center transition-opacity duration-200">
    <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col transform transition-all duration-200">
        <div class="flex items-center justify-between p-6 border-b border-gray-100">
            <h2 class="text-xl font-semibold text-gray-900">Prompt Improvement Suggestions</h2>
            <button onclick="closeSuggestionsModal()" class="w-9 h-9 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors duration-150">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        <div id="suggestions-content" class="p-6 overflow-y-auto flex-1"></div>
        <div class="p-4 border-t border-gray-100 flex justify-end">
            <button onclick="closeSuggestionsModal()" class="bg-gray-100 text-gray-700 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-200 transition-colors duration-200">Close</button>
        </div>
    </div>
</div>
```

**Step 4: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): modernize news list header and modal styling"
```

---

## Task 3: Update News List - Card Rendering

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Update renderNewsList function**

Replace the article card template in renderNewsList (lines 147-168):
```javascript
return `
<div id="row-${article.id}" class="bg-white rounded-lg shadow p-4">
    <div class="flex justify-between items-start">
        <div class="flex-1">
            <h3 class="font-semibold text-lg ${headlineClass}"
                ${headlineClick}>
                ${article.headline}
            </h3>
            <p id="content-${article.id}" class="text-gray-600 text-sm mt-1"
               data-full="${escapeHtml(article.content)}"
               data-expanded="false">
                ${displayContent}
            </p>
        </div>
        <button onclick="startWorkflow('${article.id}')"
                class="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800 ml-4">
            Start AI Workflow
        </button>
    </div>
    <div class="ai-insight hidden mt-4"></div>
</div>
`}).join('');
```

With:
```javascript
return `
<div id="row-${article.id}" class="bg-white rounded-xl border border-gray-100 shadow-sm p-6 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
    <div class="flex justify-between items-start gap-6">
        <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-lg text-gray-900 leading-snug ${headlineClass}"
                ${headlineClick}>
                ${article.headline}
            </h3>
            <p id="content-${article.id}" class="text-gray-500 text-sm mt-2 leading-relaxed"
               data-full="${escapeHtml(article.content)}"
               data-expanded="false">
                ${displayContent}
            </p>
        </div>
        <button onclick="startWorkflow('${article.id}')"
                class="flex-shrink-0 bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-red-500 active:bg-red-700 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 focus:ring-2 focus:ring-red-600/50 focus:ring-offset-2 focus:outline-none">
            Start AI Workflow
        </button>
    </div>
    <div class="ai-insight hidden mt-6"></div>
</div>
`}).join('');
```

**Step 2: Update pagination text**

Replace the pagination section (lines 170-176):
```javascript
if (data.total > data.articles.length) {
    container.innerHTML += `
        <div class="text-center text-gray-500 text-sm">
            Showing ${data.articles.length} of ${data.total} articles
        </div>
    `;
}
```

With:
```javascript
if (data.total > data.articles.length) {
    container.innerHTML += `
        <div class="text-center text-gray-400 text-sm py-4">
            Showing ${data.articles.length} of ${data.total} articles
        </div>
    `;
}
```

**Step 3: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): modernize news article cards with hover effects"
```

---

## Task 4: Update News List - AI Insight Section

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Update renderInsight function**

Replace the entire renderInsight function (lines 219-254):
```javascript
function renderInsight(articleId, insight) {
    return `
        <div class="p-4 bg-gray-50 border-t-2 border-red-600">
            <h4 class="font-semibold text-black">AI Insight</h4>
            <p><strong>Category:</strong> ${insight.category}</p>
            <p><strong>Confidence:</strong> ${(insight.confidence * 100).toFixed(0)}%</p>
            <table class="w-full mt-2 text-sm border border-gray-300">
                <thead><tr class="bg-gray-200">
                    <th class="p-2 text-left text-black">Category Excerpt</th>
                    <th class="p-2 text-left text-black">News Excerpt</th>
                    <th class="p-2 text-left text-black">Reasoning</th>
                </tr></thead>
                <tbody>
                    ${insight.reasoning_table.map(r => `
                        <tr class="border-t border-gray-300">
                            <td class="p-2">${r.category_excerpt}</td>
                            <td class="p-2">${r.news_excerpt}</td>
                            <td class="p-2">${r.reasoning}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div id="feedback-section-${articleId}" class="mt-4 p-3 bg-white border border-gray-300 rounded">
                <h5 class="font-semibold mb-2 text-black">Your Feedback (Required)</h5>
                <select id="correct-cat-${articleId}" class="w-full border border-gray-300 rounded p-2 mb-2 focus:border-red-600 focus:ring-1 focus:ring-red-600">
                    <option value="">Correct Category</option>
                </select>
                <textarea id="reasoning-${articleId}" class="w-full border border-gray-300 rounded p-2 mb-2 focus:border-red-600 focus:ring-1 focus:ring-red-600" placeholder="Your reasoning" rows="2"></textarea>
                <div class="flex gap-2">
                    <button onclick="submitFeedback('${articleId}', true)" class="px-3 py-1 bg-gray-200 text-black rounded hover:bg-gray-300 border border-gray-400">👍 Correct</button>
                    <button onclick="submitFeedback('${articleId}', false)" class="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-800">👎 Incorrect</button>
                </div>
            </div>
        </div>
    `;
}
```

With:
```javascript
function renderInsight(articleId, insight) {
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
                                <td class="px-4 py-3 text-gray-600">${r.category_excerpt}</td>
                                <td class="px-4 py-3 text-gray-600">${r.news_excerpt}</td>
                                <td class="px-4 py-3 text-gray-600">${r.reasoning}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div id="feedback-section-${articleId}" class="mt-5 p-5 bg-white border border-gray-200 rounded-xl">
                <h5 class="font-semibold mb-4 text-gray-900">Your Feedback</h5>
                <div class="space-y-4">
                    <select id="correct-cat-${articleId}" class="w-full border border-gray-200 rounded-lg px-4 py-2.5 bg-white text-gray-900 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150">
                        <option value="">Select correct category</option>
                    </select>
                    <textarea id="reasoning-${articleId}" class="w-full border border-gray-200 rounded-lg px-4 py-2.5 bg-white text-gray-900 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150 resize-none" placeholder="Explain your reasoning..." rows="3"></textarea>
                    <div class="flex gap-3">
                        <button onclick="submitFeedback('${articleId}', true)" class="flex-1 bg-green-50 text-green-700 border border-green-200 px-4 py-2.5 rounded-lg font-medium hover:bg-green-100 hover:border-green-300 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200">
                            <span class="flex items-center justify-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                Correct
                            </span>
                        </button>
                        <button onclick="submitFeedback('${articleId}', false)" class="flex-1 bg-red-50 text-red-700 border border-red-200 px-4 py-2.5 rounded-lg font-medium hover:bg-red-100 hover:border-red-300 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200">
                            <span class="flex items-center justify-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                Incorrect
                            </span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}
```

**Step 2: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): modernize AI insight section with progress bar and refined feedback"
```

---

## Task 5: Update News List - Evaluation Result & Error States

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Update showInlineError function**

Replace lines 289-299:
```javascript
function showInlineError(articleId, message) {
    const feedbackSection = document.getElementById('feedback-section-' + articleId);
    const errorDiv = feedbackSection.querySelector('.inline-error');
    if (errorDiv) {
        errorDiv.remove();
    }
    const newError = document.createElement('div');
    newError.className = 'inline-error bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded mb-2 text-sm';
    newError.textContent = message;
    feedbackSection.insertBefore(newError, feedbackSection.firstChild);
}
```

With:
```javascript
function showInlineError(articleId, message) {
    const feedbackSection = document.getElementById('feedback-section-' + articleId);
    const errorDiv = feedbackSection.querySelector('.inline-error');
    if (errorDiv) {
        errorDiv.remove();
    }
    const newError = document.createElement('div');
    newError.className = 'inline-error bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2 animate-shake';
    newError.innerHTML = `<svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg><span>${message}</span>`;
    feedbackSection.insertBefore(newError, feedbackSection.firstChild);
}
```

**Step 2: Update showEvaluationResult function**

Replace lines 301-325:
```javascript
function showEvaluationResult(articleId, report, thumbsUp) {
    const feedbackSection = document.getElementById('feedback-section-' + articleId);
    const statusIcon = thumbsUp ? '👍' : '👎';
    const statusText = thumbsUp ? 'Marked as Correct' : 'Marked as Incorrect';
    const statusClass = thumbsUp ? 'border-gray-400 bg-gray-50' : 'border-red-400 bg-red-50';

    feedbackSection.innerHTML = `
        <div class="border-l-4 ${statusClass} p-4 rounded">
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                    <span class="text-xl">${statusIcon}</span>
                    <span class="font-semibold text-black">${statusText}</span>
                </div>
                <button onclick="dismissEvaluationResult('${articleId}')"
                        class="text-gray-500 hover:text-black text-sm">
                    Dismiss
                </button>
            </div>
            <div class="bg-white border border-gray-200 rounded p-3">
                <h6 class="font-semibold text-sm text-black mb-2">Evaluation Summary</h6>
                <p class="text-gray-700 text-sm">${escapeHtml(report.summary)}</p>
            </div>
        </div>
    `;
}
```

With:
```javascript
function showEvaluationResult(articleId, report, thumbsUp) {
    const feedbackSection = document.getElementById('feedback-section-' + articleId);
    const statusText = thumbsUp ? 'Marked as Correct' : 'Marked as Incorrect';
    const statusBorder = thumbsUp ? 'border-green-500' : 'border-red-500';
    const statusBg = thumbsUp ? 'bg-green-50' : 'bg-red-50';
    const statusIcon = thumbsUp
        ? '<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
        : '<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';

    feedbackSection.innerHTML = `
        <div class="border-l-4 ${statusBorder} ${statusBg} p-5 rounded-r-xl transition-all duration-300">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    ${statusIcon}
                    <span class="font-semibold text-gray-900">${statusText}</span>
                </div>
                <button onclick="dismissEvaluationResult('${articleId}')"
                        class="text-gray-400 hover:text-gray-600 text-sm font-medium hover:bg-white/50 px-3 py-1 rounded-lg transition-colors duration-150">
                    Dismiss
                </button>
            </div>
            <div class="bg-white/70 border border-gray-200 rounded-xl p-4">
                <h6 class="font-medium text-sm text-gray-700 mb-2">Evaluation Summary</h6>
                <p class="text-gray-600 text-sm leading-relaxed">${escapeHtml(report.summary)}</p>
            </div>
        </div>
    `;
}
```

**Step 3: Add shake animation to Tailwind config in base.html**

In `base.html`, update the Tailwind config style block (after the utilities layer) to add:
```html
<style type="text/tailwindcss">
    @layer utilities {
        .transition-base {
            @apply transition-all duration-200 ease-out;
        }
        .transition-fast {
            @apply transition-all duration-150 ease-out;
        }
        .transition-slow {
            @apply transition-all duration-300 ease-out;
        }
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-4px); }
        75% { transform: translateX(4px); }
    }
    .animate-shake {
        animation: shake 0.3s ease-in-out;
    }
</style>
```

**Step 4: Commit**

```bash
git add app/templates/base.html app/templates/news_list.html
git commit -m "feat(ui): modernize evaluation results and error states"
```

---

## Task 6: Update News List - Suggestions Modal Content

**Files:**
- Modify: `app/templates/news_list.html`

**Step 1: Update suggestions content rendering in suggestImprovements function**

Replace the modal content innerHTML (lines 365-401) inside the `.then(data => {...})` block:
```javascript
document.getElementById('suggestions-content').innerHTML = `
    <h3 class="font-semibold mt-4 text-black">Category Suggestions</h3>
    <ul class="list-disc pl-5 text-gray-700">
        ${categorySuggestions.map(s => `<li><span class="font-medium">${s.category}:</span> ${s.rationale}</li>`).join('')}
    </ul>
    <h3 class="font-semibold mt-4 text-black">Priority</h3>
    <ol class="list-decimal pl-5 text-gray-700">
        ${priorityOrder.map(p => `<li>${p}</li>`).join('')}
    </ol>
    <details class="mt-4">
        <summary class="font-semibold cursor-pointer text-black hover:text-red-600">Updated Categories (changed only)</summary>
        ...
    </details>
    ...
`;
```

With:
```javascript
document.getElementById('suggestions-content').innerHTML = `
    <div class="space-y-6">
        <div>
            <h3 class="font-semibold text-gray-900 mb-3">Category Suggestions</h3>
            <ul class="space-y-2">
                ${categorySuggestions.map(s => `
                    <li class="flex gap-3 text-sm">
                        <span class="font-medium text-gray-900 flex-shrink-0">${s.category}:</span>
                        <span class="text-gray-600">${s.rationale}</span>
                    </li>
                `).join('')}
            </ul>
        </div>
        <div>
            <h3 class="font-semibold text-gray-900 mb-3">Priority Order</h3>
            <ol class="space-y-1.5">
                ${priorityOrder.map((p, i) => `
                    <li class="flex items-center gap-3 text-sm">
                        <span class="w-6 h-6 flex items-center justify-center bg-red-100 text-red-700 rounded-full text-xs font-medium">${i + 1}</span>
                        <span class="text-gray-700">${p}</span>
                    </li>
                `).join('')}
            </ol>
        </div>
        <details class="group border border-gray-200 rounded-xl overflow-hidden">
            <summary class="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors duration-150">
                <span class="font-medium text-gray-900">Updated Categories</span>
                <svg class="w-5 h-5 text-gray-500 transform group-open:rotate-180 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </summary>
            <div class="p-4 space-y-3">
                <textarea id="updated-categories-text" readonly
                          class="w-full h-40 border border-gray-200 rounded-lg p-3 text-sm bg-gray-50 focus:outline-none resize-none"></textarea>
                <div id="updated-categories-note" class="text-xs text-gray-500"></div>
                <button id="copy-updated-categories"
                        onclick="copyText('updated-categories-text')"
                        class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors duration-150">
                    Copy to clipboard
                </button>
            </div>
        </details>
        <details class="group border border-gray-200 rounded-xl overflow-hidden">
            <summary class="flex items-center justify-between px-4 py-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors duration-150">
                <span class="font-medium text-gray-900">Updated Few-Shot Examples</span>
                <svg class="w-5 h-5 text-gray-500 transform group-open:rotate-180 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </summary>
            <div class="p-4 space-y-3">
                <textarea id="updated-fewshots-text" readonly
                          class="w-full h-56 border border-gray-200 rounded-lg p-3 text-sm bg-gray-50 focus:outline-none resize-none"></textarea>
                <div id="updated-fewshots-note" class="text-xs text-gray-500"></div>
                <button id="copy-updated-fewshots"
                        onclick="copyText('updated-fewshots-text')"
                        class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors duration-150">
                    Copy to clipboard
                </button>
                <div id="updated-fewshots-removals" class="text-sm text-gray-600"></div>
            </div>
        </details>
    </div>
`;
```

**Step 2: Commit**

```bash
git add app/templates/news_list.html
git commit -m "feat(ui): modernize suggestions modal content styling"
```

---

## Task 7: Update Prompts Page - Tabs & Container

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Update page title**

Replace line 6:
```html
<h1 class="text-2xl font-bold mb-6 text-black">Prompt Editor</h1>
```

With:
```html
<h1 class="text-2xl font-semibold mb-8 text-gray-900">Prompt Editor</h1>
```

**Step 2: Update main container and tabs**

Replace lines 8-33:
```html
<div class="bg-white rounded-lg shadow">
    <div class="border-b border-gray-200">
        <nav class="flex">
            <button onclick="showTab('categories')" id="tab-categories"
                    class="px-6 py-3 border-b-2 border-red-600 text-red-600">
                Category Definitions
            </button>
            <button onclick="showTab('fewshots')" id="tab-fewshots"
                    class="px-6 py-3 border-b-2 border-transparent text-gray-500 hover:text-black">
                Few-Shot Examples
            </button>
        </nav>
    </div>

    <div id="panel-categories" class="p-6">
        <div id="categories-list" class="space-y-4 mb-4"></div>
        <button onclick="addCategory()" class="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800">+ Add Category</button>
        <button onclick="saveCategories()" class="bg-gray-800 text-white px-4 py-2 rounded ml-2 hover:bg-black">Save</button>
    </div>

    <div id="panel-fewshots" class="p-6 hidden">
        <div id="fewshots-list" class="space-y-4 mb-4"></div>
        <button onclick="addFewShot()" class="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800">+ Add Example</button>
        <button onclick="saveFewShots()" class="bg-gray-800 text-white px-4 py-2 rounded ml-2 hover:bg-black">Save</button>
    </div>
</div>
```

With:
```html
<div class="bg-white rounded-xl border border-gray-100 shadow-sm">
    <div class="border-b border-gray-100">
        <nav class="flex gap-1 px-2 pt-2">
            <button onclick="showTab('categories')" id="tab-categories"
                    class="px-5 py-3 rounded-t-lg font-medium text-sm border-b-2 border-red-600 text-red-600 bg-red-50/50 transition-all duration-200">
                Category Definitions
            </button>
            <button onclick="showTab('fewshots')" id="tab-fewshots"
                    class="px-5 py-3 rounded-t-lg font-medium text-sm border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-all duration-200">
                Few-Shot Examples
            </button>
        </nav>
    </div>

    <div id="panel-categories" class="p-6">
        <div id="categories-list" class="space-y-5 mb-6"></div>
        <div class="flex gap-3">
            <button onclick="addCategory()" class="bg-gray-100 text-gray-700 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-200 active:bg-gray-300 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0">
                + Add Category
            </button>
            <button onclick="saveCategories()" class="bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-red-500 active:bg-red-700 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 focus:ring-2 focus:ring-red-600/50 focus:ring-offset-2 focus:outline-none">
                Save Changes
            </button>
        </div>
    </div>

    <div id="panel-fewshots" class="p-6 hidden">
        <div id="fewshots-list" class="space-y-5 mb-6"></div>
        <div class="flex gap-3">
            <button onclick="addFewShot()" class="bg-gray-100 text-gray-700 px-5 py-2.5 rounded-lg font-medium hover:bg-gray-200 active:bg-gray-300 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0">
                + Add Example
            </button>
            <button onclick="saveFewShots()" class="bg-red-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-red-500 active:bg-red-700 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 focus:ring-2 focus:ring-red-600/50 focus:ring-offset-2 focus:outline-none">
                Save Changes
            </button>
        </div>
    </div>
</div>
```

**Step 3: Update showTab function to handle new tab styles**

Replace the showTab function (lines 41-52):
```javascript
function showTab(tab) {
    document.getElementById('panel-categories').classList.toggle('hidden', tab !== 'categories');
    document.getElementById('panel-fewshots').classList.toggle('hidden', tab !== 'fewshots');
    document.getElementById('tab-categories').classList.toggle('border-red-600', tab === 'categories');
    document.getElementById('tab-categories').classList.toggle('text-red-600', tab === 'categories');
    document.getElementById('tab-categories').classList.toggle('border-transparent', tab !== 'categories');
    document.getElementById('tab-categories').classList.toggle('text-gray-500', tab !== 'categories');
    document.getElementById('tab-fewshots').classList.toggle('border-red-600', tab === 'fewshots');
    document.getElementById('tab-fewshots').classList.toggle('text-red-600', tab === 'fewshots');
    document.getElementById('tab-fewshots').classList.toggle('border-transparent', tab !== 'fewshots');
    document.getElementById('tab-fewshots').classList.toggle('text-gray-500', tab !== 'fewshots');
}
```

With:
```javascript
function showTab(tab) {
    document.getElementById('panel-categories').classList.toggle('hidden', tab !== 'categories');
    document.getElementById('panel-fewshots').classList.toggle('hidden', tab !== 'fewshots');

    const catTab = document.getElementById('tab-categories');
    const fsTab = document.getElementById('tab-fewshots');

    catTab.classList.toggle('border-red-600', tab === 'categories');
    catTab.classList.toggle('text-red-600', tab === 'categories');
    catTab.classList.toggle('bg-red-50/50', tab === 'categories');
    catTab.classList.toggle('border-transparent', tab !== 'categories');
    catTab.classList.toggle('text-gray-500', tab !== 'categories');
    catTab.classList.toggle('bg-transparent', tab !== 'categories');

    fsTab.classList.toggle('border-red-600', tab === 'fewshots');
    fsTab.classList.toggle('text-red-600', tab === 'fewshots');
    fsTab.classList.toggle('bg-red-50/50', tab === 'fewshots');
    fsTab.classList.toggle('border-transparent', tab !== 'fewshots');
    fsTab.classList.toggle('text-gray-500', tab !== 'fewshots');
    fsTab.classList.toggle('bg-transparent', tab !== 'fewshots');
}
```

**Step 4: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): modernize prompts page tabs and container"
```

---

## Task 8: Update Prompts Page - Category & Few-Shot Cards

**Files:**
- Modify: `app/templates/prompts.html`

**Step 1: Update renderCategories function**

Replace lines 73-83:
```javascript
function renderCategories() {
    document.getElementById('categories-list').innerHTML = categories.map((c, i) => `
        <div class="border rounded p-4">
            <input type="text" value="${escapeHtml(c.name)}" onchange="categories[${i}].name=this.value"
                   class="w-full border rounded p-2 mb-2" placeholder="Category Name">
            <textarea onchange="categories[${i}].definition=this.value"
                      class="w-full border rounded p-2" rows="3" placeholder="Definition">${escapeHtml(c.definition)}</textarea>
            <button onclick="categories.splice(${i},1);renderCategories()" class="text-red-600 text-sm mt-2">Remove</button>
        </div>
    `).join('');
}
```

With:
```javascript
function renderCategories() {
    document.getElementById('categories-list').innerHTML = categories.map((c, i) => `
        <div class="border border-gray-200 rounded-xl p-5 hover:border-gray-300 transition-colors duration-200">
            <input type="text" value="${escapeHtml(c.name)}" onchange="categories[${i}].name=this.value"
                   class="w-full border border-gray-200 rounded-lg px-4 py-2.5 mb-3 text-gray-900 font-medium focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150" placeholder="Category Name">
            <textarea onchange="categories[${i}].definition=this.value"
                      class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-gray-700 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150 resize-none" rows="3" placeholder="Definition...">${escapeHtml(c.definition)}</textarea>
            <button onclick="categories.splice(${i},1);renderCategories()" class="mt-3 text-red-600 text-sm font-medium hover:text-red-700 hover:underline transition-colors duration-150">Remove</button>
        </div>
    `).join('');
}
```

**Step 2: Update renderFewShots function**

Replace lines 103-116:
```javascript
function renderFewShots() {
    document.getElementById('fewshots-list').innerHTML = fewShots.map((f, i) => `
        <div class="border rounded p-4">
            <input type="text" value="${escapeHtml(f.id)}" readonly class="w-full border rounded p-2 mb-2 bg-gray-100">
            <textarea onchange="fewShots[${i}].news_content=this.value"
                      class="w-full border rounded p-2 mb-2" rows="2" placeholder="News Content">${escapeHtml(f.news_content)}</textarea>
            <input type="text" value="${escapeHtml(f.category)}" onchange="fewShots[${i}].category=this.value"
                   class="w-full border rounded p-2 mb-2" placeholder="Category">
            <textarea onchange="fewShots[${i}].reasoning=this.value"
                      class="w-full border rounded p-2" rows="2" placeholder="Reasoning">${escapeHtml(f.reasoning)}</textarea>
            <button onclick="fewShots.splice(${i},1);renderFewShots()" class="text-red-600 text-sm mt-2">Remove</button>
        </div>
    `).join('');
}
```

With:
```javascript
function renderFewShots() {
    document.getElementById('fewshots-list').innerHTML = fewShots.map((f, i) => `
        <div class="border border-gray-200 rounded-xl p-5 hover:border-gray-300 transition-colors duration-200">
            <div class="flex items-center gap-2 mb-3">
                <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">ID:</span>
                <input type="text" value="${escapeHtml(f.id)}" readonly class="flex-1 border border-gray-100 rounded-lg px-3 py-1.5 text-sm bg-gray-50 text-gray-500">
            </div>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">News Content</label>
                    <textarea onchange="fewShots[${i}].news_content=this.value"
                              class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-gray-700 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150 resize-none" rows="2" placeholder="Enter news content...">${escapeHtml(f.news_content)}</textarea>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">Category</label>
                    <input type="text" value="${escapeHtml(f.category)}" onchange="fewShots[${i}].category=this.value"
                           class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-gray-700 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150" placeholder="Category name">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5">Reasoning</label>
                    <textarea onchange="fewShots[${i}].reasoning=this.value"
                              class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-gray-700 focus:border-red-600 focus:ring-2 focus:ring-red-600/20 focus:outline-none transition-all duration-150 resize-none" rows="2" placeholder="Explain the categorization...">${escapeHtml(f.reasoning)}</textarea>
                </div>
            </div>
            <button onclick="fewShots.splice(${i},1);renderFewShots()" class="mt-4 text-red-600 text-sm font-medium hover:text-red-700 hover:underline transition-colors duration-150">Remove example</button>
        </div>
    `).join('');
}
```

**Step 3: Commit**

```bash
git add app/templates/prompts.html
git commit -m "feat(ui): modernize category and few-shot card styling"
```

---

## Task 9: Final Review & Testing

**Files:**
- All template files

**Step 1: Verify all changes work together**

Run the application and manually test:
1. Header sticks on scroll with blur effect
2. Shadow appears on header when scrolled
3. Cards have hover lift effect
4. Buttons have proper hover/active states
5. Modal opens/closes with animations
6. Forms have proper focus states
7. Navigation links highlight correctly
8. Responsive behavior works at different viewport sizes

**Step 2: Fix any visual inconsistencies**

Check for:
- Consistent spacing throughout
- Proper color usage (red-600 for primary, gray scale for secondary)
- Smooth transitions on all interactive elements

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore(ui): final polish and consistency pass"
```

---

## Summary of Changes

| File | Changes |
|------|---------|
| `base.html` | Sticky blur header, custom transitions, scroll shadow JS, refined loader |
| `news_list.html` | Modernized cards, AI insight with progress bar, feedback buttons, modal styling |
| `prompts.html` | Tab redesign, card styling, form inputs, button hierarchy |

**Total commits:** 9
