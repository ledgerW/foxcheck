document.addEventListener('DOMContentLoaded', () => {
    const totalArticles = document.getElementById('total-articles');
    const totalUsers = document.getElementById('total-users');
    const totalStatements = document.getElementById('total-statements');
    const articlesTableBody = document.getElementById('articles-table-body');
    const refreshBtn = document.getElementById('refresh-btn');
    const loadingSpinner = document.querySelector('.loading-spinner');

    async function loadDashboardData() {
        try {
            loadingSpinner.style.display = 'block';

            // Load articles with admin privileges
            const response = await fetch('/api/articles?include_inactive=true', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load articles');
            }

            const articles = await response.json();
            updateArticlesTable(articles);
            totalArticles.textContent = articles.length;

            // Load other stats
            const statsResponse = await fetch('/api/admin/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                totalUsers.textContent = stats.total_users;
                totalStatements.textContent = stats.total_statements;
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            showError('Failed to load dashboard data');
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function updateArticlesTable(articles) {
        articlesTableBody.innerHTML = articles.map(article => `
            <tr>
                <td>${article.title}</td>
                <td>${article.domain || 'N/A'}</td>
                <td>${article.authors || 'Unknown'}</td>
                <td>
                    <span class="badge ${article.is_active ? 'bg-success' : 'bg-danger'}">
                        ${article.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary" onclick="toggleArticleStatus(${article.id}, ${!article.is_active})">
                            ${article.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <a href="/articles/${article.id}" class="btn btn-sm btn-outline-secondary">
                            View
                        </a>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async function toggleArticleStatus(articleId, newStatus) {
        try {
            const response = await fetch(`/api/articles/${articleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({
                    is_active: newStatus
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update article status');
            }

            // Refresh the dashboard
            loadDashboardData();
        } catch (error) {
            console.error('Error updating article status:', error);
            alert('Failed to update article status');
        }
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger mt-3';
        errorDiv.textContent = message;
        document.querySelector('.article-management').prepend(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }

    // Make toggleArticleStatus available globally
    window.toggleArticleStatus = toggleArticleStatus;

    // Event listeners
    refreshBtn.addEventListener('click', loadDashboardData);

    // Initial load
    loadDashboardData();
});
