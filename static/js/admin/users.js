document.addEventListener('DOMContentLoaded', () => {
    loadUsers();

    // Event listeners for edit user modal
    const editUserModal = document.getElementById('editUserModal');
    const saveUserChangesBtn = document.getElementById('save-user-changes');
    
    saveUserChangesBtn.addEventListener('click', saveUserChanges);
});

async function loadUsers() {
    const tableBody = document.getElementById('users-table-body');
    const loadingDiv = document.createElement('tr');
    loadingDiv.innerHTML = `
        <td colspan="7" class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </td>
    `;
    tableBody.innerHTML = '';
    tableBody.appendChild(loadingDiv);

    try {
        const response = await fetch('/api/admin/users', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load users');
        }

        const users = await response.json();
        displayUsers(users);
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users. Please try again.');
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = users.map(user => `
        <tr data-id="${user.id}">
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>
                <span class="badge ${user.is_active ? 'bg-success' : 'bg-danger'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <span class="badge ${user.is_admin ? 'bg-primary' : 'bg-secondary'}">
                    ${user.is_admin ? 'Admin' : 'User'}
                </span>
            </td>
            <td>${new Date(user.created_at).toLocaleString()}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="editUser(${user.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function editUser(userId) {
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    const loadingSpinner = document.getElementById('edit-user-loading');
    const modalContent = document.getElementById('edit-user-form');
    const modalError = document.getElementById('edit-user-error');

    try {
        // Show loading state
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (modalContent) modalContent.style.display = 'none';
        if (modalError) modalError.style.display = 'none';
        
        modal.show();

        const response = await fetch(`/api/admin/users/${userId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch user data');
        }

        const user = await response.json();
        
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-username').value = user.username;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-is-active').checked = user.is_active;
        document.getElementById('edit-is-admin').checked = user.is_admin;
        
        // Hide loading, show content
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        if (modalContent) modalContent.style.display = 'block';
    } catch (error) {
        console.error('Error loading user:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = 'Failed to load user data. Please try again.';
        }
        if (loadingSpinner) loadingSpinner.style.display = 'none';
    }
}

async function saveUserChanges() {
    const userId = document.getElementById('edit-user-id').value;
    const saveButton = document.getElementById('save-user-changes');
    const modalError = document.getElementById('edit-user-error');
    
    const userData = {
        username: document.getElementById('edit-username').value,
        email: document.getElementById('edit-email').value,
        is_active: document.getElementById('edit-is-active').checked,
        is_admin: document.getElementById('edit-is-admin').checked
    };

    try {
        // Disable save button and show loading state
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        }
        if (modalError) modalError.style.display = 'none';

        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(userData)
        });

        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
            modal.hide();
            showSuccess('User updated successfully');
            loadUsers(); // Refresh the users list
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update user');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        if (modalError) {
            modalError.style.display = 'block';
            modalError.textContent = error.message || 'Failed to update user. Please try again.';
        }
    } finally {
        // Reset save button state
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.innerHTML = 'Save changes';
        }
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            showSuccess('User deleted successfully');
            loadUsers(); // Refresh the users list
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showError(error.message || 'Failed to delete user. Please try again.');
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