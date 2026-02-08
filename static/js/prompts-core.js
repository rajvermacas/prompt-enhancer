    let categories = [];
    let fewShots = [];
    let feedbacks = [];
    let suggestionsData = null;
    let feedbacksLoaded = false;
    let currentSuggestionView = 'by-type';
    let systemPromptContent = '';
    let promptVersions = {
        categories: null,
        fewshots: null,
        systemprompt: null,
    };
    let promptHistory = {
        categories: [],
        fewshots: [],
        systemprompt: [],
    };

    const PROMPT_HISTORY_CONFIG = {
        categories: {
            endpoint: 'categories',
            contentKey: 'categories',
            successMessage: 'Categories restored!',
        },
        fewshots: {
            endpoint: 'few-shots',
            contentKey: 'examples',
            successMessage: 'Few-shots restored!',
        },
        systemprompt: {
            endpoint: 'system-prompt',
            contentKey: 'content',
            successMessage: 'System prompt restored!',
        },
    };

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

    function loadPrompts() {
        const wsId = getWorkspaceId();
        if (!wsId) return;

        fetch(`/api/workspaces/${wsId}/prompts/categories`)
            .then(r => r.json())
            .then(data => {
                categories = data.categories;
                promptVersions.categories = data.version;
                renderCategories();
                renderVersionBadge('categories');
                loadPromptHistory('categories');
            });

        fetch(`/api/workspaces/${wsId}/prompts/few-shots`)
            .then(r => r.json())
            .then(data => {
                fewShots = data.examples;
                promptVersions.fewshots = data.version;
                renderFewShots();
                renderVersionBadge('fewshots');
                loadPromptHistory('fewshots');
            });

        loadSystemPrompt();
    }

    function loadSystemPrompt() {
        const wsId = getWorkspaceId();
        if (!wsId) return;

        fetch(`/api/workspaces/${wsId}/prompts/system-prompt`)
            .then(r => r.json())
            .then(data => {
                systemPromptContent = data.content || '';
                promptVersions.systemprompt = data.version;
                document.getElementById('system-prompt-content').value = systemPromptContent;
                renderVersionBadge('systemprompt');
                loadPromptHistory('systemprompt');
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
        .then(response => {
            if (response.status === 202) {
                alert('Sent for approval!');
                return;
            } else if (response.status === 409) {
                return response.json().then(data => {
                    alert('Error: ' + data.detail);
                });
            } else {
                return response.json().then(data => {
                    systemPromptContent = data.content;
                    promptVersions.systemprompt = data.version;
                    document.getElementById('system-prompt-content').value = systemPromptContent;
                    renderVersionBadge('systemprompt');
                    loadPromptHistory('systemprompt');
                    alert('System prompt saved!');
                });
            }
        })
        .catch(err => {
            alert('Error saving system prompt: ' + err.message);
        });
    }

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

    function addCategory() {
        categories.push({name: '', definition: ''});
        renderCategories();
    }

    function saveCategories() {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }
        fetch(`/api/workspaces/${wsId}/prompts/categories`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({categories})
        })
        .then(response => {
            if (response.status === 202) {
                alert('Sent for approval!');
            } else if (response.status === 409) {
                return response.json().then(data => {
                    alert('Error: ' + data.detail);
                });
            } else {
                return response.json().then(data => {
                    categories = data.categories;
                    promptVersions.categories = data.version;
                    renderCategories();
                    renderVersionBadge('categories');
                    loadPromptHistory('categories');
                    alert('Categories saved!');
                });
            }
        })
        .catch(err => alert('Error saving categories: ' + err.message));
    }

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

    function addFewShot() {
        fewShots.push({id: 'ex-' + Date.now(), news_content: '', category: '', reasoning: ''});
        renderFewShots();
    }

    function saveFewShots() {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }
        fetch(`/api/workspaces/${wsId}/prompts/few-shots`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({examples: fewShots})
        })
        .then(response => {
            if (response.status === 202) {
                alert('Sent for approval!');
            } else if (response.status === 409) {
                return response.json().then(data => {
                    alert('Error: ' + data.detail);
                });
            } else {
                return response.json().then(data => {
                    fewShots = data.examples;
                    promptVersions.fewshots = data.version;
                    renderFewShots();
                    renderVersionBadge('fewshots');
                    loadPromptHistory('fewshots');
                    alert('Few-shots saved!');
                });
            }
        })
        .catch(err => alert('Error saving few-shots: ' + err.message));
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    function renderVersionBadge(type) {
        const badge = document.getElementById(`${type}-version-badge`);
        const version = promptVersions[type];
        if (version === null) {
            badge.textContent = '';
            return;
        }
        badge.textContent = `Current version: v${version}`;
    }

    function loadPromptHistory(type) {
        const wsId = getWorkspaceId();
        if (!wsId) return;

        const config = getPromptHistoryConfig(type);
        fetch(`/api/workspaces/${wsId}/prompts/${config.endpoint}/history`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load ${config.endpoint} history`);
                }
                return response.json();
            })
            .then(data => {
                promptHistory[type] = data;
                renderPromptHistoryOptions(type);
            })
            .catch(err => {
                const meta = document.getElementById(`${type}-history-meta`);
                meta.textContent = '';
                renderDiffStatus(type, `Error loading history: ${err.message}`, true);
            });
    }

    function renderPromptHistoryOptions(type) {
        const select = document.getElementById(`${type}-history-select`);
        const history = promptHistory[type];
        if (history.length === 0) {
            select.innerHTML = '<option value="">No history available</option>';
            renderHistoryDetails(type);
            return;
        }

        select.innerHTML = history.map(entry => (
            `<option value="${entry.version}">Version ${entry.version} (${escapeHtml(entry.updated_at)})</option>`
        )).join('');
        renderHistoryDetails(type);
    }

    function renderHistoryDetails(type) {
        const select = document.getElementById(`${type}-history-select`);
        const meta = document.getElementById(`${type}-history-meta`);
        const diff = document.getElementById(`${type}-history-diff`);
        const selectedVersion = Number(select.value);
        const history = promptHistory[type];
        const selected = history.find(entry => entry.version === selectedVersion);

        if (!selected) {
            meta.textContent = '';
            renderDiffStatus(type, 'Select a version to inspect diff details.', false);
            return;
        }

        const previous = history.find(entry => entry.version === selected.version - 1);
        meta.textContent = `Updated by ${selected.updated_by} via ${selected.source}` +
            ` at ${selected.updated_at}`;
        const historyDiff = getPromptHistoryDiffModule();
        const rows = historyDiff.buildPromptHistoryDiffRows(
            type,
            selected.content,
            previous ? previous.content : null,
        );
        renderDiffRows(diff, rows);
    }

    function getPromptHistoryDiffModule() {
        const historyDiff = window.PromptHistoryDiff;
        if (!historyDiff || typeof historyDiff.buildPromptHistoryDiffRows !== 'function') {
            throw new Error('PromptHistoryDiff module is required');
        }
        return historyDiff;
    }

    function renderDiffStatus(type, message, isError) {
        const diff = document.getElementById(`${type}-history-diff`);
        const textColor = isError ? 'text-red-700' : 'text-gray-500';
        diff.innerHTML = `<div class="px-3 py-2 ${textColor}">${escapeHtml(message)}</div>`;
    }

    function renderDiffRows(diffElement, rows) {
        if (!Array.isArray(rows)) {
            throw new Error('rows must be an array');
        }
        diffElement.innerHTML = rows.map(row => renderDiffRow(row)).join('');
    }

    function renderDiffRow(row) {
        if (!row || !row.type) {
            throw new Error('Diff row requires a type');
        }
        if (row.type === 'hunk-header') {
            if (row.text === undefined || row.text === null) {
                throw new Error('hunk-header row requires text');
            }
            return `
                <div class="px-3 py-1 bg-gray-800 text-gray-100 whitespace-pre">
                    ${escapeHtml(row.text)}
                </div>
            `;
        }
        if (row.type === 'info') {
            if (row.text === undefined || row.text === null) {
                throw new Error('info row requires text');
            }
            return `
                <div class="px-3 py-2 text-gray-500 italic whitespace-pre">
                    ${escapeHtml(row.text)}
                </div>
            `;
        }
        if (row.type === 'line') {
            return renderSideBySideDiffRow(row);
        }
        throw new Error(`Unsupported diff row type: ${row.type}`);
    }

    function renderSideBySideDiffRow(row) {
        if (!('left' in row) || !('right' in row)) {
            throw new Error('line row requires left and right fields');
        }
        return `
            <div class="grid grid-cols-2 border-t border-gray-100">
                ${renderDiffSideCell(row.left, 'left')}
                ${renderDiffSideCell(row.right, 'right')}
            </div>
        `;
    }

    function renderDiffSideCell(side, column) {
        if (column !== 'left' && column !== 'right') {
            throw new Error(`Unknown diff column: ${column}`);
        }
        if (side === null) {
            return `
                <div class="grid grid-cols-[3rem_1fr] gap-2 px-3 py-0.5 bg-gray-50 text-gray-300">
                    <span class="text-right text-[11px] select-none"></span>
                    <span class="whitespace-pre"></span>
                </div>
            `;
        }
        if (!side.kind || side.text === undefined || side.lineNumber === undefined) {
            throw new Error('Diff side requires kind, text, and lineNumber');
        }
        const sideClass = getDiffSideCellClass(side.kind);
        const prefix = getDiffKindPrefix(side.kind);
        const prefixClass = getDiffPrefixClass(side.kind);
        return `
            <div class="grid grid-cols-[3rem_1fr] gap-2 px-3 py-0.5 ${sideClass}">
                <span class="text-right text-[11px] text-gray-500 select-none">${formatDiffLineNumber(side.lineNumber)}</span>
                <span class="whitespace-pre">
                    <span class="select-none ${prefixClass}">${prefix}</span>${escapeHtml(side.text)}
                </span>
            </div>
        `;
    }

    function getDiffSideCellClass(kind) {
        if (kind === 'context') return 'bg-white text-gray-800';
        if (kind === 'added') return 'bg-green-50 text-green-900';
        if (kind === 'removed') return 'bg-red-50 text-red-900';
        throw new Error(`Unknown diff kind: ${kind}`);
    }

    function getDiffKindPrefix(kind) {
        if (kind === 'context') return ' ';
        if (kind === 'added') return '+';
        if (kind === 'removed') return '-';
        throw new Error(`Unknown diff kind: ${kind}`);
    }

    function getDiffPrefixClass(kind) {
        if (kind === 'context') return 'text-gray-500';
        if (kind === 'added') return 'text-green-700';
        if (kind === 'removed') return 'text-red-700';
        throw new Error(`Unknown diff kind: ${kind}`);
    }

    function formatDiffLineNumber(lineNumber) {
        if (lineNumber === null || lineNumber === undefined) {
            return '';
        }
        return String(lineNumber);
    }

    function restorePromptVersion(type) {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }

        const selectedVersion = Number(
            document.getElementById(`${type}-history-select`).value
        );
        if (!selectedVersion) {
            alert('Please select a version to restore');
            return;
        }

        const config = getPromptHistoryConfig(type);
        fetch(`/api/workspaces/${wsId}/prompts/${config.endpoint}/restore`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({version: selectedVersion}),
        })
        .then(response => {
            if (response.status === 202) {
                alert('Sent for approval!');
                return;
            }
            if (response.status === 409 || response.status === 404) {
                return response.json().then(data => {
                    throw new Error(data.detail);
                });
            }
            if (!response.ok) {
                throw new Error('Restore failed');
            }
            return response.json().then(data => {
                applyRestoredPrompt(type, data);
                alert(config.successMessage);
            });
        })
        .catch(err => alert('Error restoring version: ' + err.message));
    }

    function applyRestoredPrompt(type, data) {
        const config = getPromptHistoryConfig(type);
        promptVersions[type] = data.version;
        if (type === 'categories') {
            categories = data[config.contentKey];
            renderCategories();
        } else if (type === 'fewshots') {
            fewShots = data[config.contentKey];
            renderFewShots();
        } else if (type === 'systemprompt') {
            systemPromptContent = data[config.contentKey];
            document.getElementById('system-prompt-content').value = systemPromptContent;
        }
        renderVersionBadge(type);
        loadPromptHistory(type);
    }

    function getPromptHistoryConfig(type) {
        const config = PROMPT_HISTORY_CONFIG[type];
        if (!config) {
            throw new Error(`Unknown prompt history type: ${type}`);
        }
        return config;
    }

    document.getElementById('workspace-selector').addEventListener('change', () => {
        feedbacksLoaded = false;
        loadPrompts();
    });
    if (getWorkspaceId()) loadPrompts();
