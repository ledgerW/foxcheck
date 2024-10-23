document.addEventListener('DOMContentLoaded', () => {
    const articlesContainer = document.getElementById('articles-container');
    const newArticleBtn = document.getElementById('new-article-btn');
    
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
            const response = await fetch('/articles', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const articles = await response.json();
                displayArticles(articles);
            } else {
                console.error('Failed to load articles');
            }
        } catch (error) {
            console.error('Error loading articles:', error);
        }
    }

    function displayArticles(articles) {
        articlesContainer.innerHTML = articles.map(article => `
            <div class="col">
                <div class="card article-card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${article.title}</h5>
                        <p class="card-text">${article.text.substring(0, 200)}...</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">Published: ${new Date(article.date).toLocaleDateString()}</small>
                            <a href="/articles/${article.id}" class="btn btn-primary btn-sm">Read More</a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    checkAuthAndUpdateUI();
    loadArticles();

    newArticleBtn.addEventListener('click', () => {
        // TODO: Implement new article creation
        alert('New article creation will be implemented in the next phase');
    });
});
