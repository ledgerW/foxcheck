document.addEventListener('DOMContentLoaded', () => {
    loadUsers();

    // Event listeners for edit user modal
    const editUserModal = document.getElementById('editUserModal');
    const saveUserChangesBtn = document.getElementById('save-user-changes');
    
    saveUserChangesBtn.addEventListener('click', saveUserChanges);
});

async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const users = await response.json();
            displayUsers(users);
        } else {
            console.error('Failed to load users');
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = users.map(user => `
        <tr>
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
                <button class="btn btn-sm btn-primary" onclick="editUser(${user.id})">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function editUser(userId) {
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    const user = getUserById(userId);
    if (user) {
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-username').value = user.username;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-is-active').checked = user.is_active;
        document.getElementById('edit-is-admin').checked = user.is_admin;
        modal.show();
    }
}

async function saveUserChanges() {
    const userId = document.getElementById('edit-user-id').value;
    const userData = {
        username: document.getElementById('edit-username').value,
        email: document.getElementById('edit-email').value,
        is_active: document.getElementById('edit-is-active').checked,
        is_admin: document.getElementById('edit-is-admin').checked
    };

    try {
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
            loadUsers();
        } else {
            console.error('Failed to update user');
        }
    } catch (error) {
        console.error('Error updating user:', error);
    }
}

function getUserById(userId) {
    const row = document.querySelector(`#users-table-body tr td:first-child[data-id="${userId}"]`)?.parentElement;
    if (!row) return null;

    return {
        id: userId,
        username: row.children[1].textContent,
        email: row.children[2].textContent,
        is_active: row.children[3].querySelector('.badge').classList.contains('bg-success'),
        is_admin: row.children[4].querySelector('.badge').classList.contains('bg-primary')
    };
}
