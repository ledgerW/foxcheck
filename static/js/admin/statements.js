document.addEventListener('DOMContentLoaded', () => {
    loadStatements();

    // Event listeners for edit statement modal
    const saveStatementChangesBtn = document.getElementById('save-statement-changes');
    saveStatementChangesBtn.addEventListener('click', saveStatementChanges);
});

async function loadStatements() {
    const tableBody = document.getElementById('statements-table-body');
    const loadingDiv = document.createElement('tr');
    loadingDiv.innerHTML = `
        <td colspan="6" class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </td>
    `;
    tableBody.innerHTML = '';
    tableBody.appendChild(loadingDiv);

    try {
        const response = await fetch('/api/admin/statements', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load statements');
        }

        const statements = await response.json();
        displayStatements(statements);
    } catch (error) {
        console.error('Error loading statements:', error);
        showError('Failed to load statements. Please try again.');
    }
}

function displayStatements(statements) {
    const tbody = document.getElementById('statements-table-body');
    tbody.innerHTML = statements.map(statement => `
        <tr data-id="${statement.id}">
            <td>${statement.id}</td>
            <td>${statement.content}</td>
            <td>
                <span class="badge ${getVerdictBadgeClass(statement.verdict)}">
                    ${statement.verdict || 'Unverified'}
                </span>
            </td>
            <td>
                <a href="/articles/${statement.article_id}" target="_blank">
                    ${statement.article?.title || `Article #${statement.article_id}`}
                </a>
            </td>
            <td>${new Date(statement.created_at).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="editStatement(${statement.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteStatement(${statement.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getVerdictBadgeClass(verdict) {
    switch (verdict) {
        case 'True': return 'bg-success';
        case 'False': return 'bg-danger';
        case 'Mostly True': return 'bg-warning';
        case 'Mostly False': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

async function editStatement(statementId) {
    const modal = new bootstrap.Modal(document.getElementById('editStatementModal'));
    const loadingSpinner = document.getElementById('edit-statement-loading');
    const modalContent = document.getElementById('edit-statement-form');
    const modalError = document.getElementById('edit-statement-error');

    try {
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (modalContent) modalContent.style.display = 'none';
        if (modalError) modalError.style.display = 'none';
        
        modal.show();

        const response = await fetch(`/api/admin/statements/${statementId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch statement data');
        }

        const statement = await response.json();
        
        document.getElementById('edit-statement-id').value = statement.id;
        document.getElementById('edit-content').value = statement.content;
        document.getElementById('edit-verdict').value = statement.verdict || 'Unverified';
        document.getElementById('edit-explanation').value = statement.explanation || '';
        document.getElementById('edit-references').value = statement.references || '';
        
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        if (modalContent) modalContent.style.display = 'block';
    } catch (error) {
        console.error('Error loading statement:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = 'Failed to load statement data. Please try again.';
        }
        if (loadingSpinner) loadingSpinner.style.display = 'none';
    }
}

async function deleteStatement(statementId) {
    if (!confirm('Are you sure you want to delete this statement? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/statements/${statementId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            showSuccess('Statement deleted successfully');
            loadStatements();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete statement');
        }
    } catch (error) {
        console.error('Error deleting statement:', error);
        showError(error.message || 'Failed to delete statement. Please try again.');
    }
}

async function saveStatementChanges() {
    const statementId = document.getElementById('edit-statement-id').value;
    const saveButton = document.getElementById('save-statement-changes');
    const modalError = document.getElementById('edit-statement-error');
    
    let references;
    try {
        const referencesText = document.getElementById('edit-references').value;
        references = referencesText ? JSON.parse(referencesText) : [];
        
        if (!Array.isArray(references)) {
            throw new Error('References must be an array');
        }
        
        references = references.map(ref => {
            if (!ref.title || !ref.source) {
                throw new Error('Each reference must have a title and source');
            }
            return {
                title: ref.title,
                source: ref.source,
                summary: ref.summary || ''
            };
        });
    } catch (error) {
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = 'Invalid JSON format in references field: ' + error.message;
        }
        return;
    }

    const statementData = {
        content: document.getElementById('edit-content').value || null,
        verdict: document.getElementById('edit-verdict').value || null,
        explanation: document.getElementById('edit-explanation').value || null,
        references: references
    };

    try {
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        }
        if (modalError) modalError.style.display = 'none';

        const response = await fetch(`/api/admin/statements/${statementId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(statementData)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editStatementModal'));
            modal.hide();
            showSuccess('Statement updated successfully');
            loadStatements();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update statement');
        }
    } catch (error) {
        console.error('Error updating statement:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = error.message || 'Failed to update statement. Please try again.';
        }
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = 'Save changes';
        }
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