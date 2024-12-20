document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    const loadingSpinner = document.getElementById('loading-spinner');

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    async function performSearch() {
        const query = searchInput.value.trim();
        if (query === '') {
            displayError('Please enter a statement to check.');
            return;
        }

        searchResults.innerHTML = '';
        loadingSpinner.style.display = 'inline-block';

        try {
            const response = await fetch('/api/check_statement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ statement: query })
            });

            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'An error occurred while checking the statement');
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            displayError(error.message);
            console.error('Statement check error:', error);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    function displayResults(result) {
        const resultHtml = `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">Verdict: ${result.verdict}</h5>
                    <p class="card-text">${result.explanation}</p>
                    <h6>References:</h6>
                    <ul>
                        ${result.references.map(ref => `
                            <li>
                                <a href="${ref.source}" target="_blank">${ref.title}</a>
                                <p>${ref.summary}</p>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;

        searchResults.innerHTML = resultHtml;
    }

    function displayError(message) {
        searchResults.innerHTML = `<p class="text-danger">${message}</p>`;
    }
});