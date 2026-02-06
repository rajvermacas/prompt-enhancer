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

    function loadFeedbacks() {
        const wsId = getWorkspaceId();
        if (!wsId) return;

        document.getElementById('feedbacks-loader').classList.remove('hidden');
        document.getElementById('source-feedbacks').innerHTML = '';

        fetch(`/api/workspaces/${wsId}/feedback-with-headlines`)
            .then(r => r.json())
            .then(data => {
                feedbacks = data;
                feedbacksLoaded = true;
                renderSourceFeedbacks(feedbacks);
                document.getElementById('feedbacks-loader').classList.add('hidden');
            })
            .catch(err => {
                document.getElementById('feedbacks-loader').classList.add('hidden');
                document.getElementById('source-feedbacks').innerHTML =
                    `<p class="text-red-500 text-sm">Error loading feedback: ${escapeHtml(err.message)}</p>`;
            });
    }

    function deleteFeedback(feedbackId) {
        if (!confirm('Are you sure you want to delete this feedback? This action cannot be undone.')) {
            return;
        }

        const wsId = getWorkspaceId();
        if (!wsId) return;

        fetch(`/api/workspaces/${wsId}/feedback/${feedbackId}`, {
            method: 'DELETE'
        })
        .then(r => {
            if (!r.ok) {
                return r.json().then(err => { throw new Error(err.detail); });
            }
            return r.json();
        })
        .then(() => {
            feedbacks = feedbacks.filter(fb => fb.id !== feedbackId);
            renderSourceFeedbacks(feedbacks);
        })
        .catch(err => {
            alert('Error deleting feedback: ' + err.message);
        });
    }

    function generateSuggestions() {
        const wsId = getWorkspaceId();
        if (!wsId) {
            alert('Please select a workspace first');
            return;
        }

        document.getElementById('suggestions-loader').classList.remove('hidden');
        document.getElementById('suggestions-content').classList.add('hidden');
        document.getElementById('suggestions-error').classList.add('hidden');
        document.getElementById('generate-suggestions-btn').disabled = true;

        fetch(`/api/workspaces/${wsId}/suggest-improvements`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
        .then(r => {
            if (!r.ok) {
                return r.json().then(err => { throw new Error(err.detail); });
            }
            return r.json();
        })
        .then(data => {
            suggestionsData = data;
            renderSuggestions(data);
            document.getElementById('suggestions-loader').classList.add('hidden');
            document.getElementById('suggestions-content').classList.remove('hidden');
        })
        .catch(err => {
            document.getElementById('suggestions-loader').classList.add('hidden');
            document.getElementById('suggestions-error').classList.remove('hidden');
            document.getElementById('suggestions-error').querySelector('div').textContent = err.message;
        })
        .finally(() => {
            document.getElementById('generate-suggestions-btn').disabled = false;
        });
    }

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

    function renderSuggestionsByFeedback(data) {
        const container = document.getElementById('suggestions-by-feedback');
        const feedbacksList = data.feedbacks || [];
        const catSuggestions = data.suggestions.category_suggestions || [];
        const fewShotSuggestions = data.suggestions.few_shot_suggestions || [];

        const cards = feedbacksList.map(fb => {
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

    function renderPriorityOrder(priorities) {
        const container = document.getElementById('priority-order');
        if (!priorities || priorities.length === 0) {
            container.innerHTML = '<li class="text-gray-500 text-sm">No priorities specified.</li>';
            return;
        }
        container.innerHTML = priorities.map(p => `<li>${escapeHtml(p)}</li>`).join('');
    }

    function renderUpdatedCategories(updatedCategories) {
        const container = document.getElementById('updated-categories-content');
        const countEl = document.getElementById('updated-categories-count');

        if (!updatedCategories || updatedCategories.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No updated categories.</p>';
            countEl.textContent = '';
            return;
        }

        countEl.textContent = `${updatedCategories.length} update${updatedCategories.length !== 1 ? 's' : ''}`;

        container.innerHTML = updatedCategories.map(cat => {
            const feedbackLinks = (cat.based_on_feedback_ids || []).map(id => {
                const fb = feedbacks.find(f => f.id === id);
                return fb
                    ? `<a href="#feedback-card-${id}" onclick="highlightFeedback('${id}')" class="text-red-600 hover:underline">${escapeHtml(fb.article_headline)}</a>`
                    : id;
            }).join(', ');

            return `
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ${escapeHtml(cat.category)}
                    </span>
                    <div class="text-sm text-gray-700 mt-3">
                        <span class="font-medium">Updated definition:</span>
                        <p class="mt-1 whitespace-pre-wrap">${escapeHtml(cat.updated_definition)}</p>
                    </div>
                    ${cat.rationale ? `
                        <div class="text-sm text-gray-600 mt-2">
                            <span class="font-medium">Rationale:</span> ${escapeHtml(cat.rationale)}
                        </div>
                    ` : ''}
                    ${feedbackLinks ? `<div class="text-xs text-gray-500 mt-2">Based on: ${feedbackLinks}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    function renderUpdatedFewShots(updatedFewShots) {
        const container = document.getElementById('updated-fewshots-content');
        const countEl = document.getElementById('updated-fewshots-count');

        if (!updatedFewShots || updatedFewShots.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No updated few-shot examples.</p>';
            countEl.textContent = '';
            return;
        }

        countEl.textContent = `${updatedFewShots.length} update${updatedFewShots.length !== 1 ? 's' : ''}`;

        const actionColors = {
            add: 'bg-green-100 text-green-800',
            modify: 'bg-yellow-100 text-yellow-800',
            remove: 'bg-red-100 text-red-800'
        };

        container.innerHTML = updatedFewShots.map(item => {
            const action = item.action || 'modify';
            const example = item.example || {};
            const colorClass = actionColors[action] || 'bg-gray-100 text-gray-800';

            if (action === 'remove') {
                return `
                    <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}">
                                ${escapeHtml(action.toUpperCase())}
                            </span>
                            <span class="text-sm font-medium text-gray-900">${escapeHtml(example.id || 'Unknown ID')}</span>
                        </div>
                        <p class="text-sm text-gray-500 italic">This example will be removed</p>
                    </div>
                `;
            }

            return `
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}">
                            ${escapeHtml(action.toUpperCase())}
                        </span>
                        <span class="text-sm font-medium text-gray-700">${escapeHtml(example.id || 'New Example')}</span>
                        ${example.category ? `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${escapeHtml(example.category)}
                            </span>
                        ` : ''}
                    </div>
                    ${example.news_content ? `
                        <div class="mb-3">
                            <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">News Content</span>
                            <p class="mt-1 text-sm text-gray-700 whitespace-pre-wrap">${escapeHtml(example.news_content)}</p>
                        </div>
                    ` : ''}
                    ${example.reasoning ? `
                        <div>
                            <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">Reasoning</span>
                            <p class="mt-1 text-sm text-gray-700 whitespace-pre-wrap">${escapeHtml(example.reasoning)}</p>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    function toggleSection(sectionId) {
        const section = document.getElementById(sectionId);
        const arrow = document.getElementById(sectionId + '-arrow');
        section.classList.toggle('hidden');
        arrow.style.transform = section.classList.contains('hidden') ? '' : 'rotate(90deg)';
    }

    function copyUpdatedCategories() {
        if (!suggestionsData || !suggestionsData.suggestions.updated_categories) {
            alert('No updated categories to copy');
            return;
        }
        const json = JSON.stringify(suggestionsData.suggestions.updated_categories, null, 2);
        navigator.clipboard.writeText(json).then(() => alert('Copied JSON to clipboard!'));
    }

    function copyUpdatedFewShots() {
        if (!suggestionsData || !suggestionsData.suggestions.updated_few_shots) {
            alert('No updated few-shot examples to copy');
            return;
        }
        const json = JSON.stringify(suggestionsData.suggestions.updated_few_shots, null, 2);
        navigator.clipboard.writeText(json).then(() => alert('Copied JSON to clipboard!'));
    }

