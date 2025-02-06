// Firebase configuration


document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('emailInput');
    const submitButton = document.getElementById('submitButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const jsonResult = document.getElementById('jsonResult');
    const errorContainer = document.getElementById('errorContainer');

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
        } catch (error) {
            showError(error.message);
            console.error('Parse error:', error);
        } finally {
            toggleLoading(false);
        }
    });

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