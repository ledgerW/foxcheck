document.addEventListener('DOMContentLoaded', () => {
    loadArticles();

    // Event listeners for edit article modal
    const saveArticleChangesBtn = document.getElementById('save-article-changes');
    saveArticleChangesBtn.addEventListener('click', saveArticleChanges);
});

async function loadArticles() {
    try {
        const response = await fetch('/api/admin/articles', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const articles = await response.json();
            displayArticles(articles);
        } else {
            console.error('Failed to load articles');
            showError('Failed to load articles. Please try again.');
        }
    } catch (error) {
        console.error('Error loading articles:', error);
        showError('An error occurred while loading articles.');
    }
}

function displayArticles(articles) {
    const tbody = document.getElementById('articles-table-body');
    tbody.innerHTML = articles.map(article => `
        <tr data-id="${article.id}">
            <td>${article.id}</td>
            <td>${article.title}</td>
            <td>${article.domain || '-'}</td>
            <td>${article.authors || '-'}</td>
            <td>
                <span class="badge ${article.is_active ? 'bg-success' : 'bg-danger'}">
                    ${article.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${new Date(article.date).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="editArticle(${article.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger me-1" onclick="deleteArticle(${article.id})">
                    <i class="bi bi-trash"></i>
                </button>
                <a href="/articles/${article.id}" class="btn btn-sm btn-info" target="_blank">
                    <i class="bi bi-eye"></i>
                </a>
            </td>
        </tr>
    `).join('');
}

async function editArticle(articleId) {
    const modal = new bootstrap.Modal(document.getElementById('editArticleModal'));
    const loadingSpinner = document.getElementById('edit-article-loading');
    const modalContent = document.getElementById('edit-article-form');
    const modalError = document.getElementById('edit-article-error');

    try {
        // Show loading state
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (modalContent) modalContent.style.display = 'none';
        if (modalError) modalError.style.display = 'none';
        
        modal.show();

        const article = await getArticleById(articleId);
        
        if (article) {
            document.getElementById('edit-article-id').value = article.id;
            document.getElementById('edit-title').value = article.title;
            document.getElementById('edit-domain').value = article.domain || '';
            document.getElementById('edit-authors').value = article.authors || '';
            document.getElementById('edit-text').value = article.text;
            document.getElementById('edit-is-active').checked = article.is_active;
            
            // Hide loading, show content
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (modalContent) modalContent.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading article:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = 'Failed to load article data. Please try again.';
        }
        if (loadingSpinner) loadingSpinner.style.display = 'none';
    }
}

async function getArticleById(articleId) {
    try {
        const response = await fetch(`/api/admin/articles/${articleId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch article data');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching article:', error);
        throw error;
    }
}

async function saveArticleChanges() {
    const articleId = document.getElementById('edit-article-id').value;
    const saveButton = document.getElementById('save-article-changes');
    const modalError = document.getElementById('edit-article-error');
    
    // Collect form data
    const articleData = {
        title: document.getElementById('edit-title').value,
        domain: document.getElementById('edit-domain').value,
        authors: document.getElementById('edit-authors').value,
        text: document.getElementById('edit-text').value,
        is_active: document.getElementById('edit-is-active').checked
    };

    try {
        // Disable save button and show loading state
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        }
        if (modalError) modalError.style.display = 'none';

        const response = await fetch(`/api/admin/articles/${articleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(articleData)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editArticleModal'));
            modal.hide();
            loadArticles(); // Refresh the articles list
            showSuccess('Article updated successfully');
        } else {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to update article');
        }
    } catch (error) {
        console.error('Error updating article:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = error.message || 'Failed to update article. Please try again.';
        }
    } finally {
        // Reset save button state
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = 'Save changes';
        }
    }
}

async function deleteArticle(articleId) {
    if (!confirm('Are you sure you want to delete this article? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/articles/${articleId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            showSuccess('Article deleted successfully');
            loadArticles(); // Refresh the articles list
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete article');
        }
    } catch (error) {
        console.error('Error deleting article:', error);
        showError(error.message || 'Failed to delete article. Please try again.');
    }
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container-fluid').insertBefore(alertDiv, document.querySelector('.table-responsive'));
}

function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container-fluid').insertBefore(alertDiv, document.querySelector('.table-responsive'));
}