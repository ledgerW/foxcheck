document.addEventListener('DOMContentLoaded', async () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');
    const loggedOutMenu = document.getElementById('logged-out-menu');
    const loggedInMenu = document.getElementById('logged-in-menu');
    const usernameDisplay = document.getElementById('username-display');
    const adminDashboardLink = document.getElementById('admin-dashboard-link');

    // Check if we're on login/register page and redirect if already logged in
    if (window.location.pathname === '/login' || window.location.pathname === '/register') {
        const token = localStorage.getItem('access_token');
        if (token) {
            const authStatus = await checkAuthStatus();
            if (authStatus.authenticated) {
                // If user is admin and was trying to access admin page before login
                const previousPath = sessionStorage.getItem('previous_path');
                if (previousPath && previousPath.startsWith('/admin') && authStatus.is_admin) {
                    window.location.href = previousPath;
                    sessionStorage.removeItem('previous_path');
                } else {
                    window.location.href = '/';
                }
            }
        }
    }

    // Check if we're on an admin page and verify admin access
    if (window.location.pathname.startsWith('/admin')) {
        const adminCheck = await checkAdminAccess();
        if (!adminCheck) {
            return;
        }
    }

    // Add admin dashboard link handler
    if (adminDashboardLink) {
        adminDashboardLink.addEventListener('click', async (e) => {
            e.preventDefault();
            const token = localStorage.getItem('access_token');
            
            try {
                const response = await fetch('/api/auth/status', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.authenticated && data.is_admin) {
                        window.location.href = '/admin';
                    } else {
                        alert('Unauthorized: Admin access required');
                        window.location.href = '/';
                    }
                } else {
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Error checking admin access:', error);
                window.location.href = '/';
            }
        });
    }

    async function checkAuthStatus() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                updateUIForLoggedOutState();
                return { authenticated: false };
            }

            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    updateUIForLoggedInState(data.username, data.is_admin);
                    return data;
                }
            }
            localStorage.removeItem('access_token');
            updateUIForLoggedOutState();
            return { authenticated: false };
        } catch (error) {
            console.error('Error checking auth status:', error);
            localStorage.removeItem('access_token');
            updateUIForLoggedOutState();
            return { authenticated: false };
        }
    }

    async function checkAdminAccess() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                sessionStorage.setItem('previous_path', window.location.pathname);
                window.location.href = '/login';
                return false;
            }

            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (!data.authenticated || !data.is_admin) {
                    alert('Unauthorized: Admin access required');
                    window.location.href = '/';
                    return false;
                }
                return true;
            } else {
                localStorage.removeItem('access_token');
                sessionStorage.setItem('previous_path', window.location.pathname);
                window.location.href = '/login';
                return false;
            }
        } catch (error) {
            console.error('Error checking admin access:', error);
            localStorage.removeItem('access_token');
            sessionStorage.setItem('previous_path', window.location.pathname);
            window.location.href = '/login';
            return false;
        }
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }

    async function handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/users/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password }),
            });

            if (response.ok) {
                alert('Registration successful! Please log in.');
                window.location.href = '/login';
            } else {
                const errorData = await response.json();
                alert(`Registration failed: ${errorData.detail}`);
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('An error occurred during registration. Please try again.');
        }
    }

    async function handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/users/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': username,
                    'password': password,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                const authStatus = await checkAuthStatus();
                if (authStatus.authenticated) {
                    // If user is admin and was trying to access admin page before login
                    const previousPath = sessionStorage.getItem('previous_path');
                    if (previousPath && previousPath.startsWith('/admin') && authStatus.is_admin) {
                        window.location.href = previousPath;
                        sessionStorage.removeItem('previous_path');
                    } else {
                        window.location.href = '/';
                    }
                }
            } else {
                const errorData = await response.json();
                alert(`Login failed: ${errorData.detail}`);
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('An error occurred during login. Please try again.');
        }
    }

    async function handleLogout() {
        localStorage.removeItem('access_token');
        await checkAuthStatus();
        window.location.href = '/';
    }

    function updateUIForLoggedInState(username, isAdmin) {
        if (loggedOutMenu) loggedOutMenu.style.display = 'none';
        if (loggedInMenu) loggedInMenu.style.display = 'block';
        if (usernameDisplay) usernameDisplay.textContent = username;
        
        // Update admin menu items visibility
        const adminMenuItems = document.querySelectorAll('.admin-menu-item');
        adminMenuItems.forEach(item => {
            item.style.display = isAdmin ? 'block' : 'none';
        });
    }

    function updateUIForLoggedOutState() {
        if (loggedOutMenu) loggedOutMenu.style.display = 'block';
        if (loggedInMenu) loggedInMenu.style.display = 'none';
        if (usernameDisplay) usernameDisplay.textContent = '';

        // If on admin page, store the path and redirect
        if (window.location.pathname.startsWith('/admin')) {
            sessionStorage.setItem('previous_path', window.location.pathname);
            window.location.href = '/login';
        }
    }

    // Initial auth status check
    checkAuthStatus();
});
