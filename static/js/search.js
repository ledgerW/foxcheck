document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    async function performSearch() {
        const query = searchInput.value.trim();
        if (query === '') return;

        searchResults.innerHTML = '<p>Searching...</p>';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            if (!response.ok) {
                throw new Error('Search request failed');
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            searchResults.innerHTML = '<p>An error occurred while searching. Please try again.</p>';
            console.error('Search error:', error);
        }
    }

    function displayResults(results) {
        if (results.length === 0) {
            searchResults.innerHTML = '<p>No results found.</p>';
            return;
        }

        const resultHtml = results.map(result => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${result.title}</h5>
                    <p class="card-text">${result.snippet}</p>
                    <a href="${result.link}" class="btn btn-primary" target="_blank">Read more</a>
                </div>
            </div>
        `).join('');

        searchResults.innerHTML = resultHtml;
    }
});
