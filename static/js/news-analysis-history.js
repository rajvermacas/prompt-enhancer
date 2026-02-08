(function () {
    const HISTORY_PAGE_LIMIT = 10;

    function getState(articleId) {
        if (!window.analysisHistoryState) {
            window.analysisHistoryState = {};
        }
        if (!window.analysisHistoryState[articleId]) {
            window.analysisHistoryState[articleId] = {
                expanded: false,
                selectedRunId: null,
                pageData: null,
                page: 1,
            };
        }
        return window.analysisHistoryState[articleId];
    }

    function requireHistoryContainer(articleId) {
        const container = document.getElementById('analysis-history-' + articleId);
        if (!container) {
            throw new Error('Analysis history container not found for article ' + articleId);
        }
        return container;
    }

    function formatTimestamp(isoText) {
        const timestamp = new Date(isoText);
        return timestamp.toLocaleString();
    }

    function renderSnapshot(insight) {
        const userRequestedAnalysis = insight.user_requested_analysis
            ? `
                <div class="mt-3 p-3 bg-white border border-gray-200 rounded-lg">
                    <h6 class="font-semibold text-gray-900 mb-1">User-Requested Analysis</h6>
                    <p class="text-gray-700 text-sm whitespace-pre-wrap">${escapeHtml(insight.user_requested_analysis)}</p>
                </div>
            `
            : '';

        return `
            <div class="mt-3 border border-gray-200 rounded-lg p-4 bg-white">
                <div class="flex items-center justify-between mb-3">
                    <h6 class="font-semibold text-gray-900">Selected Previous Run</h6>
                    <span class="bg-red-50 text-red-700 px-2 py-0.5 rounded text-xs font-medium">${escapeHtml(insight.category)}</span>
                </div>
                <div class="text-xs text-gray-600 mb-3">Confidence ${(insight.confidence * 100).toFixed(0)}%</div>
                <div class="overflow-x-auto rounded-lg border border-gray-200">
                    <table class="w-full text-xs">
                        <thead>
                            <tr class="bg-gray-100">
                                <th class="px-3 py-2 text-left text-gray-700 font-medium">Category Excerpt</th>
                                <th class="px-3 py-2 text-left text-gray-700 font-medium">News Excerpt</th>
                                <th class="px-3 py-2 text-left text-gray-700 font-medium">Reasoning</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            ${insight.reasoning_table.map((row) => `
                                <tr>
                                    <td class="px-3 py-2 text-gray-600">${escapeHtml(row.category_excerpt)}</td>
                                    <td class="px-3 py-2 text-gray-600">${escapeHtml(row.news_excerpt)}</td>
                                    <td class="px-3 py-2 text-gray-600">${escapeHtml(row.reasoning)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${userRequestedAnalysis}
            </div>
        `;
    }

    function buildHistoryMarkup(articleId) {
        const state = getState(articleId);
        const pageData = state.pageData;
        const count = pageData ? pageData.total : 0;
        const expandedClass = state.expanded ? '' : 'hidden';

        if (!pageData || count === 0) {
            return '';
        }

        const selectedRun = state.selectedRunId
            ? pageData.items.find((item) => item.id === state.selectedRunId)
            : null;

        const previousDisabled = pageData.page <= 1 ? 'disabled' : '';
        const nextDisabled = pageData.has_next ? '' : 'disabled';

        return `
            <div class="mt-4 border border-gray-200 rounded-lg bg-gray-50">
                <button type="button"
                        onclick="toggleAnalysisHistory('${articleId}')"
                        class="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-100 rounded-lg">
                    <span class="text-sm font-medium text-gray-800">Previous runs (${count})</span>
                    <span class="text-gray-500 text-xs">${state.expanded ? 'Hide' : 'Show'}</span>
                </button>
                <div class="px-4 pb-4 ${expandedClass}">
                    <div class="space-y-2 max-h-48 overflow-y-auto">
                        ${pageData.items.map((item) => `
                            <button type="button"
                                    onclick="selectAnalysisHistoryRun('${articleId}', '${item.id}')"
                                    class="w-full text-left p-2 border rounded-md bg-white hover:bg-red-50 ${state.selectedRunId === item.id ? 'border-red-300' : 'border-gray-200'}">
                                <div class="text-xs text-gray-500">${formatTimestamp(item.created_at)}</div>
                                <div class="text-sm font-medium text-gray-800">${escapeHtml(item.insight.category)} • ${(item.insight.confidence * 100).toFixed(0)}%</div>
                            </button>
                        `).join('')}
                    </div>
                    <div class="mt-3 flex items-center justify-between">
                        <button type="button"
                                onclick="changeAnalysisHistoryPage('${articleId}', ${pageData.page - 1})"
                                class="text-xs px-2 py-1 rounded border border-gray-200 bg-white disabled:opacity-40"
                                ${previousDisabled}>Previous</button>
                        <span class="text-xs text-gray-500">Page ${pageData.page}</span>
                        <button type="button"
                                onclick="changeAnalysisHistoryPage('${articleId}', ${pageData.page + 1})"
                                class="text-xs px-2 py-1 rounded border border-gray-200 bg-white disabled:opacity-40"
                                ${nextDisabled}>Next</button>
                    </div>
                    ${selectedRun ? renderSnapshot(selectedRun.insight) : ''}
                </div>
            </div>
        `;
    }

    window.loadAnalysisHistory = function loadAnalysisHistory(articleId, page) {
        const wsId = getWorkspaceId();
        const state = getState(articleId);
        state.page = page;

        fetch(`/api/workspaces/${wsId}/analysis-history?article_id=${articleId}&page=${page}&limit=${HISTORY_PAGE_LIMIT}&exclude_latest=true`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Failed to load analysis history');
                }
                return response.json();
            })
            .then((pageData) => {
                state.pageData = pageData;
                if (pageData.items.length > 0) {
                    state.selectedRunId = pageData.items[0].id;
                } else {
                    state.selectedRunId = null;
                }
                requireHistoryContainer(articleId).innerHTML = buildHistoryMarkup(articleId);
            })
            .catch(() => {
                requireHistoryContainer(articleId).innerHTML =
                    '<div class="mt-4 text-sm text-red-600">Failed to load previous runs.</div>';
            });
    };

    window.toggleAnalysisHistory = function toggleAnalysisHistory(articleId) {
        const state = getState(articleId);
        state.expanded = !state.expanded;
        requireHistoryContainer(articleId).innerHTML = buildHistoryMarkup(articleId);
    };

    window.selectAnalysisHistoryRun = function selectAnalysisHistoryRun(articleId, runId) {
        const state = getState(articleId);
        state.selectedRunId = runId;
        requireHistoryContainer(articleId).innerHTML = buildHistoryMarkup(articleId);
    };

    window.changeAnalysisHistoryPage = function changeAnalysisHistoryPage(articleId, page) {
        if (page < 1) {
            throw new Error('page must be >= 1');
        }
        loadAnalysisHistory(articleId, page);
    };
})();
