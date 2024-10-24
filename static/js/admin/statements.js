document.addEventListener('DOMContentLoaded', () => {
    loadStatements();

    // Event listeners for edit statement modal
    const saveStatementChangesBtn = document.getElementById('save-statement-changes');
    saveStatementChangesBtn.addEventListener('click', saveStatementChanges);
});

async function loadStatements() {
    try {
        const response = await fetch('/api/admin/statements', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const statements = await response.json();
            displayStatements(statements);
        } else {
            console.error('Failed to load statements');
        }
    } catch (error) {
        console.error('Error loading statements:', error);
    }
}

function displayStatements(statements) {
    const tbody = document.getElementById('statements-table-body');
    tbody.innerHTML = statements.map(statement => `
        <tr>
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
                <button class="btn btn-sm btn-primary" onclick="editStatement(${statement.id})">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function getVerdictBadgeClass(verdict) {
    switch (verdict) {
        case 'True': return 'bg-success';
        case 'False': return 'bg-danger';
        case 'Partially True': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

function editStatement(statementId) {
    const modal = new bootstrap.Modal(document.getElementById('editStatementModal'));
    const statement = getStatementById(statementId);
    if (statement) {
        document.getElementById('edit-statement-id').value = statement.id;
        document.getElementById('edit-content').value = statement.content;
        document.getElementById('edit-verdict').value = statement.verdict || 'Unverified';
        document.getElementById('edit-explanation').value = statement.explanation || '';
        document.getElementById('edit-references').value = JSON.stringify(statement.references || [], null, 2);
        modal.show();
    }
}

async function saveStatementChanges() {
    const statementId = document.getElementById('edit-statement-id').value;
    let references;
    try {
        references = JSON.parse(document.getElementById('edit-references').value);
    } catch (error) {
        alert('Invalid JSON format in references');
        return;
    }

    const statementData = {
        content: document.getElementById('edit-content').value,
        verdict: document.getElementById('edit-verdict').value,
        explanation: document.getElementById('edit-explanation').value,
        references: references
    };

    try {
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
            loadStatements();
        } else {
            console.error('Failed to update statement');
        }
    } catch (error) {
        console.error('Error updating statement:', error);
    }
}

function getStatementById(statementId) {
    const row = document.querySelector(`#statements-table-body tr td:first-child[data-id="${statementId}"]`)?.parentElement;
    if (!row) return null;

    return {
        id: statementId,
        content: row.children[1].textContent,
        verdict: row.children[2].querySelector('.badge').textContent.trim(),
        explanation: '', // This will be filled when editing
        references: [] // This will be filled when editing
    };
}
