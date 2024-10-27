document.addEventListener('DOMContentLoaded', async () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');
    const loggedOutMenu = document.getElementById('logged-out-menu');
    const loggedInMenu = document.getElementById('logged-in-menu');
    const usernameDisplay = document.getElementById('username-display');
    const adminDashboardLink = document.getElementById('admin-dashboard-link');
    const adminUsersLink = document.getElementById('admin-users-link');

    const buttonIds = ['admin-dashboard-link', 'admin-users-link', 'admin-articles-link', 'admin-statements-link'];

    buttonIds.forEach(id => {
        const button = document.getElementById(id);
        if (button) { // Check if the element exists
            button.addEventListener('click', async (e) => {
                e.preventDefault();  // Prevent default action
                await checkAdminAccess(button);  // Pass the clicked button element
            });
        }
    });

    // Check admin access immediately if on the admin page (refresh scenario)
    if (window.location.pathname.startsWith('/admin')) {
        const adminCheck = await checkAdminAccess();
        if (!adminCheck) {
            return;
        }
    }

    // Check if we're on login/register page and redirect if already logged in
    if (window.location.pathname === '/login' || window.location.pathname === '/register') {
        const token = localStorage.getItem('access_token');
        if (token) {
            const authStatus = await checkAuthStatus();
            if (authStatus.authenticated) {
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

    async function checkAdminAccess(clickedButton) {
        console.log("Button clicked:", clickedButton.id);
        const pathMap = {
            'admin-dashboard-link': '/admin',
            'admin-users-link': '/admin/users',
            'admin-articles-link': '/admin/articles',
            'admin-statements-link': '/admin/statements'
        };

        // Get the path associated with the clicked button's ID
        const path = pathMap[clickedButton.id];
        
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';  // Redirect to login if no token
            return false;
        }

        try {
            const response = await fetch(path, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                // Load the admin page content
                document.open();
                document.write(await response.text());
                document.close();
                return true;
            } else {
                // Handle unauthorized or forbidden responses
                if (response.status === 401) {
                    window.location.href = '/login'; // Redirect to login if unauthorized
                } else {
                    window.location.href = '/'; // Redirect to home for other errors
                }
                return false;
            }
        } catch (error) {
            console.error('Error accessing admin page:', error);
            window.location.href = '/';
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
