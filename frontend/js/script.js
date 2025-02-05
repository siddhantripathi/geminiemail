// Firebase configuration


document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('emailInput');
    const submitButton = document.getElementById('submitButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const jsonResult = document.getElementById('jsonResult');
    const errorContainer = document.getElementById('errorContainer');
    const historyContainer = document.getElementById('historyContainer');

    // Load history on page load
    loadHistory();

    submitButton.addEventListener('click', async () => {
        const emailText = emailInput.value.trim();
        
        if (!emailText) {
            showError('Please enter an email to parse');
            return;
        }

        toggleLoading(true);
        clearResults();

        try {
            const response = await fetch('/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ email: emailText })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            showResult(data);
            await loadHistory();
        } catch (error) {
            showError(error.message);
            console.error('Parse error:', error);
        } finally {
            toggleLoading(false);
        }
    });

    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const history = await response.json();
            displayHistory(history);
        } catch (error) {
            console.error('Error loading history:', error);
            historyContainer.innerHTML = `
                <div class="p-4 text-red-600">
                    Failed to load history. Please try refreshing the page.
                </div>
            `;
        }
    }

    function displayHistory(history) {
        if (!history.length) {
            historyContainer.innerHTML = `
                <div class="p-4 text-gray-500">
                    No parsed emails yet. Try parsing your first email above!
                </div>
            `;
            return;
        }

        historyContainer.innerHTML = history.map(item => `
            <div class="border-b p-4 hover:bg-gray-50">
                <div class="font-semibold">${escapeHtml(item.reply_type || 'Unknown')}</div>
                <div class="text-sm text-gray-600">
                    ${new Date(item.created_at).toLocaleString()}
                </div>
                <div class="mt-2 text-sm">
                    ${item.proposed_time ? `Proposed: ${new Date(item.proposed_time).toLocaleString()}` : ''}
                    ${item.delegate_to ? `<br>Delegate: ${escapeHtml(item.delegate_to)}` : ''}
                    ${item.additional_notes ? `<br>Notes: ${escapeHtml(item.additional_notes)}` : ''}
                </div>
            </div>
        `).join('');
    }

    function escapeHtml(unsafe) {
        return unsafe
            ? unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;")
            : '';
    }

    function showResult(data) {
        resultContainer.classList.remove('hidden');
        jsonResult.textContent = JSON.stringify(data, null, 2);
        jsonResult.classList.add('language-json');
    }

    function showError(message) {
        errorContainer.classList.remove('hidden');
        errorContainer.textContent = message;
    }

    function clearResults() {
        resultContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        jsonResult.textContent = '';
    }

    function toggleLoading(show) {
        submitButton.disabled = show;
        loadingIndicator.classList.toggle('hidden', !show);
        submitButton.textContent = show ? 'Processing...' : 'Parse Email';
    }
});