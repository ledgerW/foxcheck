document.addEventListener('DOMContentLoaded', () => {
    const articlesContainer = document.getElementById('articles-container');
    const newArticleBtn = document.getElementById('new-article-btn');
    const loadingSpinner = document.querySelector('.loading-spinner');
    
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
            loadingSpinner.style.display = 'block';

            const response = await fetch('/api/articles');

            if (!response.ok) {
                throw new Error(`Failed to load articles: ${response.statusText}`);
            }

            const articles = await response.json();
            displayArticles(articles);
        } catch (error) {
            displayError(error.message);
        } finally {
            loadingSpinner.style.display = 'none';
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

    function truncateText(text, maxLength = 300) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }

    function displayArticles(articles) {
        if (!articles.length) {
            articlesContainer.innerHTML = `
                <div class="alert alert-info">
                    No articles found. Be the first to create one!
                </div>`;
            return;
        }

        articlesContainer.innerHTML = articles.map(article => `
            <div class="card article-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h2 class="card-title h4">${article.title}</h2>
                        <small class="text-muted">${article.domain || ''}</small>
                    </div>
                    <div class="text-muted mb-3">
                        ${article.authors ? `By ${article.authors} • ` : ''}
                        ${formatDate(article.date)}
                    </div>
                    <p class="card-text mb-4">${truncateText(article.text)}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${article.statements ? `
                                <span class="badge bg-secondary me-2">
                                    ${article.statements.length} Statements
                                </span>
                            ` : ''}
                        </div>
                        <a href="/articles/${article.id}" class="btn btn-outline-primary">Read More</a>
                    </div>
                </div>
            </div>
        `).join('');
    }

    function displayError(message) {
        articlesContainer.innerHTML = `
            <div class="alert alert-danger">
                <h5 class="alert-heading">Error loading articles</h5>
                <p class="mb-0">${message}</p>
            </div>`;
    }

    checkAuthAndUpdateUI();
    loadArticles();

    newArticleBtn.addEventListener('click', () => {
        alert('New article creation will be implemented in the next phase');
    });
});
