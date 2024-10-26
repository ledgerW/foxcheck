document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');
    const logoutButtonMobile = document.getElementById('logout-button-mobile');
    const loggedOutMenu = document.getElementById('logged-out-menu');
    const loggedInMenu = document.getElementById('logged-in-menu');
    const loggedOutMenuMobile = document.getElementById('logged-out-menu-mobile');
    const loggedInMenuMobile = document.getElementById('logged-in-menu-mobile');
    const usernameDisplay = document.getElementById('username-display');
    const usernameDisplayMobile = document.getElementById('username-display-mobile');

    // Add admin access check function
    async function checkAdminAccess() {
        try {
            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (!data.authenticated || !data.is_admin) {
                    window.location.href = '/';
                }
            } else {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error checking admin access:', error);
            window.location.href = '/login';
        }
    }

    // Check if we're on login/register page and redirect if already logged in
    if (window.location.pathname === '/login' || window.location.pathname === '/register') {
        const token = localStorage.getItem('access_token');
        if (token) {
            // Verify the token is valid before redirecting
            checkAuthStatus().then(data => {
                if (data.authenticated) {
                    window.location.href = '/';
                }
            });
        }
    }

    // Check if we're on an admin page and verify admin access
    if (window.location.pathname.startsWith('/admin')) {
        checkAdminAccess();
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

    if (logoutButtonMobile) {
        logoutButtonMobile.addEventListener('click', handleLogout);
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
                    window.location.href = '/';
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
                } else {
                    localStorage.removeItem('access_token');
                    updateUIForLoggedOutState();
                    return { authenticated: false };
                }
            } else {
                if (response.status === 401) {
                    localStorage.removeItem('access_token');
                }
                updateUIForLoggedOutState();
                return { authenticated: false };
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            localStorage.removeItem('access_token');
            updateUIForLoggedOutState();
            return { authenticated: false };
        }
    }

    function updateUIForLoggedInState(username, isAdmin) {
        if (loggedOutMenu) loggedOutMenu.style.display = 'none';
        if (loggedInMenu) loggedInMenu.style.display = 'block';
        if (loggedOutMenuMobile) loggedOutMenuMobile.style.display = 'none';
        if (loggedInMenuMobile) loggedInMenuMobile.style.display = 'block';
        if (usernameDisplay) usernameDisplay.textContent = username;
        if (usernameDisplayMobile) usernameDisplayMobile.textContent = username;
        
        // Update admin UI elements
        const adminMenuItems = document.querySelectorAll('.admin-menu-item');
        adminMenuItems.forEach(item => {
            item.style.display = isAdmin ? 'block' : 'none';
        });
    }

    function updateUIForLoggedOutState() {
        if (loggedOutMenu) loggedOutMenu.style.display = 'block';
        if (loggedInMenu) loggedInMenu.style.display = 'none';
        if (loggedOutMenuMobile) loggedOutMenuMobile.style.display = 'block';
        if (loggedInMenuMobile) loggedInMenuMobile.style.display = 'none';
        if (usernameDisplay) usernameDisplay.textContent = '';
        if (usernameDisplayMobile) usernameDisplayMobile.textContent = '';
    }

    // Handle mobile menu closing when clicking outside
    document.addEventListener('click', (event) => {
        const navbarCollapse = document.querySelector('.navbar-collapse');
        const navbarToggler = document.querySelector('.navbar-toggler');
        
        if (navbarCollapse && navbarCollapse.classList.contains('show') &&
            !navbarCollapse.contains(event.target) &&
            !navbarToggler.contains(event.target)) {
            navbarCollapse.classList.remove('show');
        }

        // Handle dropdown menu closing
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(event.target) && 
                !Array.from(dropdownToggles).some(toggle => toggle.contains(event.target))) {
                dropdown.classList.remove('show');
            }
        });
    });

    // Initial auth status check
    checkAuthStatus();
});
