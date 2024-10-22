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
        if (query === '') return;

        searchResults.innerHTML = '';
        loadingSpinner.style.display = 'inline-block';

        try {
            const response = await fetch('/api/check_statement', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ statement: query }),
            });

            if (!response.ok) {
                throw new Error('Statement check request failed');
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            searchResults.innerHTML = '<p>An error occurred while checking the statement. Please try again.</p>';
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
                                <a href="${ref.source_url}" target="_blank">${ref.title}</a>
                                <p>${ref.summary}</p>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;

        searchResults.innerHTML = resultHtml;
    }
});
