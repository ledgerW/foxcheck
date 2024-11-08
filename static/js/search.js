document.addEventListener('DOMContentLoaded', () => {
    const urlSearchForm = document.getElementById('url-search-form');
    const articleUrlInput = document.getElementById('article-url');
    const searchSpinner = document.getElementById('search-spinner');
    const searchError = document.getElementById('search-error');
    const loginButton = document.getElementById('login-button');
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    const logoutButton = document.getElementById('logout-button');

    urlSearchForm.addEventListener('submit', handleUrlSearch);
    logoutButton.addEventListener('click', handleLogout);

    async function handleUrlSearch(e) {
        e.preventDefault();
        
        const url = articleUrlInput.value.trim();
        if (!url) {
            showError('Please enter a valid URL');
            return;
        }

        // Show loading state
        showLoading(true);
        hideError();

        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = '/login';
                return;
            }

            const response = await fetch(`/api/articles/from_url?url=${encodeURIComponent(url)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze article');
            }

            const article = await response.json();
            if (article) {
                window.location.href = `/articles/${article.id}`;
            } else {
                showError('Could not analyze the article. Please try a different URL.');
            }
        } catch (error) {
            console.error('Error analyzing article:', error);
            showError(error.message || 'An error occurred while analyzing the article');
        } finally {
            showLoading(false);
        }
    }

    function showLoading(show) {
        searchSpinner.style.display = show ? 'block' : 'none';
        articleUrlInput.disabled = show;
        urlSearchForm.querySelector('button').disabled = show;
    }

    function showError(message) {
        searchError.textContent = message;
        searchError.style.display = 'block';
    }

    function hideError() {
        searchError.style.display = 'none';
    }

    async function checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    loginButton.style.display = 'none';
                    userInfo.style.display = 'block';
                    usernameDisplay.textContent = data.username;
                } else {
                    loginButton.style.display = 'block';
                    userInfo.style.display = 'none';
                }
            } else {
                loginButton.style.display = 'block';
                userInfo.style.display = 'none';
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            loginButton.style.display = 'block';
            userInfo.style.display = 'none';
        }
    }

    async function handleLogout() {
        localStorage.removeItem('access_token');
        await checkAuthStatus();
    }

    checkAuthStatus();
});