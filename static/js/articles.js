document.addEventListener('DOMContentLoaded', () => {
    const articlesContainer = document.getElementById('articles-container');
    const newArticleBtn = document.getElementById('new-article-btn');
    const loadingSpinner = document.createElement('div');
    loadingSpinner.className = 'text-center my-4';
    loadingSpinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading articles...</span>
        </div>
    `;
    
    async function checkAuthAndUpdateUI() {
        try {
            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    newArticleBtn.style.display = 'block';
                }
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
        }
    }

    async function loadArticles() {
        try {
            articlesContainer.innerHTML = '';
            articlesContainer.appendChild(loadingSpinner);

            const response = await fetch('/api/articles', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load articles: ${response.statusText}`);
            }

            const articles = await response.json();
            displayArticles(articles);
        } catch (error) {
            displayError(error.message);
        } finally {
            if (articlesContainer.contains(loadingSpinner)) {
                articlesContainer.removeChild(loadingSpinner);
            }
        }
    }

    function formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString(undefined, options);
    }

    function truncateText(text, maxLength = 200) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }

    function displayArticles(articles) {
        if (!articles.length) {
            articlesContainer.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">
                        No articles found. Be the first to create one!
                    </div>
                </div>`;
            return;
        }

        articlesContainer.innerHTML = articles.map(article => `
            <div class="col-md-6 mb-4">
                <div class="card article-card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title mb-3">${article.title}</h5>
                        <p class="card-text text-muted mb-3">
                            ${article.authors ? `By ${article.authors} • ` : ''}
                            ${formatDate(article.date)}
                        </p>
                        <p class="card-text mb-4">${truncateText(article.text)}</p>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            ${article.domain ? `
                                <small class="text-muted">Source: ${article.domain}</small>
                            ` : ''}
                            <a href="/articles/${article.id}" class="btn btn-outline-primary">Read More</a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function displayError(message) {
        articlesContainer.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <h5 class="alert-heading">Error loading articles</h5>
                    <p class="mb-0">${message}</p>
                </div>
            </div>`;
    }

    checkAuthAndUpdateUI();
    loadArticles();

    newArticleBtn.addEventListener('click', () => {
        // TODO: Implement new article creation
        alert('New article creation will be implemented in the next phase');
    });
});
