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
        }
    } catch (error) {
        console.error('Error loading articles:', error);
    }
}

function displayArticles(articles) {
    const tbody = document.getElementById('articles-table-body');
    tbody.innerHTML = articles.map(article => `
        <tr>
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
                <a href="/articles/${article.id}" class="btn btn-sm btn-info" target="_blank">
                    <i class="bi bi-eye"></i>
                </a>
            </td>
        </tr>
    `).join('');
}

function editArticle(articleId) {
    const modal = new bootstrap.Modal(document.getElementById('editArticleModal'));
    const article = getArticleById(articleId);
    if (article) {
        document.getElementById('edit-article-id').value = article.id;
        document.getElementById('edit-title').value = article.title;
        document.getElementById('edit-domain').value = article.domain || '';
        document.getElementById('edit-authors').value = article.authors || '';
        document.getElementById('edit-text').value = article.text;
        document.getElementById('edit-is-active').checked = article.is_active;
        modal.show();
    }
}

async function saveArticleChanges() {
    const articleId = document.getElementById('edit-article-id').value;
    const articleData = {
        title: document.getElementById('edit-title').value,
        domain: document.getElementById('edit-domain').value,
        authors: document.getElementById('edit-authors').value,
        text: document.getElementById('edit-text').value,
        is_active: document.getElementById('edit-is-active').checked
    };

    try {
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
            loadArticles();
        } else {
            console.error('Failed to update article');
        }
    } catch (error) {
        console.error('Error updating article:', error);
    }
}

function getArticleById(articleId) {
    const row = document.querySelector(`#articles-table-body tr td:first-child[data-id="${articleId}"]`)?.parentElement;
    if (!row) return null;

    return {
        id: articleId,
        title: row.children[1].textContent,
        domain: row.children[2].textContent !== '-' ? row.children[2].textContent : '',
        authors: row.children[3].textContent !== '-' ? row.children[3].textContent : '',
        text: '', // This will be filled when editing
        is_active: row.children[4].querySelector('.badge').classList.contains('bg-success')
    };
}
