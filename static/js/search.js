document.addEventListener('DOMContentLoaded', () => {
    const urlSearchForm = document.getElementById('url-search-form');
    const articleUrlInput = document.getElementById('article-url');
    const searchSpinner = document.getElementById('search-spinner');
    const searchError = document.getElementById('search-error');

    urlSearchForm.addEventListener('submit', handleUrlSearch);

    async function handleUrlSearch(e) {
        e.preventDefault();
        
        const url = articleUrlInput.value.trim();
        if (!url) {
            showError('Please enter a valid URL');
            return;
        }

        // Show loading state
        showLoading(true);
        hideError();

        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch(`/api/articles/from_url`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });


            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze article');
            }

            const article = await response.json();
            if (article) {
                window.location.href = `/articles/${article.id}`;
            } else {
                showError('Could not analyze the article. Please try a different URL.');
            }
        } catch (error) {
            console.error('Error analyzing article:', error);
            showError(error.message || 'An error occurred while analyzing the article');
        } finally {
            showLoading(false);
        }
    }

    function showLoading(show) {
        // Add show class for opacity transition
        if (show) {
            searchSpinner.classList.add('show');
        } else {
            searchSpinner.classList.remove('show');
        }
        articleUrlInput.disabled = show;
        urlSearchForm.querySelector('button').disabled = show;
    }

    function showError(message) {
        searchError.textContent = message;
        searchError.style.display = 'block';
        // Add slide down animation
        searchError.style.animation = 'slideDown 0.3s ease forwards';
    }

    function hideError() {
        // Add fade out animation
        searchError.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => {
            searchError.style.display = 'none';
        }, 300);
    }
});
