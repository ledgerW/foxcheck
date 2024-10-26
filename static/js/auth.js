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

    // Check admin access immediately if on admin page
    if (window.location.pathname.startsWith('/admin')) {
        console.log('On admin page, checking access...');
        const adminCheck = await checkAdminAccess();
        if (!adminCheck) {
            console.log('Admin check failed');
            return;
        }
        console.log('Admin access confirmed');
    }

    async function checkAdminAccess() {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.log('No token found, redirecting to login');
            sessionStorage.setItem('previous_path', window.location.pathname);
            window.location.href = '/login';
            return false;
        }

        try {
            console.log('Checking admin access...');
            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Auth status response:', data);
                if (!data.authenticated || !data.is_admin) {
                    console.log('User is not admin, redirecting to home');
                    alert('Unauthorized: Admin access required');
                    window.location.href = '/';
                    return false;
                }
                return true;
            } else {
                console.log('Auth status check failed, redirecting to login');
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

    // Update the admin dashboard link handler
    if (adminDashboardLink) {
        adminDashboardLink.addEventListener('click', async (e) => {
            e.preventDefault();
            const token = localStorage.getItem('access_token');
            
            try {
                console.log('Checking admin access for dashboard link...');
                const response = await fetch('/api/auth/status', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('Auth status response:', data);
                    if (data.authenticated && data.is_admin) {
                        window.location.href = '/admin';
                    } else {
                        console.log('User is not admin, showing alert');
                        alert('Unauthorized: Admin access required');
                        window.location.href = '/';
                    }
                } else {
                    console.log('Auth status check failed, redirecting to login');
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
                console.log('No token found, updating UI for logged out state');
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
                    console.log('User authenticated:', data.username, 'Is admin:', data.is_admin);
                    updateUIForLoggedInState(data.username, data.is_admin);
                    return data;
                }
            }
            console.log('Authentication failed, clearing token');
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
        console.log('Logging out user');
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
        console.log('UI updated for logged in state:', { username, isAdmin });
    }

    function updateUIForLoggedOutState() {
        if (loggedOutMenu) loggedOutMenu.style.display = 'block';
        if (loggedInMenu) loggedInMenu.style.display = 'none';
        if (usernameDisplay) usernameDisplay.textContent = '';

        // If on admin page, store the path and redirect
        if (window.location.pathname.startsWith('/admin')) {
            console.log('On admin page while logged out, redirecting to login');
            sessionStorage.setItem('previous_path', window.location.pathname);
            window.location.href = '/login';
        }
    }

    // Initial auth status check
    console.log('Performing initial auth status check');
    checkAuthStatus();
});
