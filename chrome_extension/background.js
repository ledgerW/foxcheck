// Function to detect if we are in a DEV or PROD environment
function getBackendURL() {
    const manifest = chrome.runtime.getManifest();
    if (manifest.key) {
        // This is PROD, use the production URL
        return "https://async-fast-api-chain-ledgerw.replit.app";
    } else {
        // This is DEV, use the development URL
        return "https://async-fast-api-chain-ledgerw.replit.app";
    }
}

// Function to handle user logout
function logoutUser() {
    return new Promise((resolve) => {
        chrome.storage.local.remove('authToken', () => {
            authToken = null;
            console.log('User logged out.');
            resolve({ success: true });
        });
    });
}

// Background service worker to handle authentication and API requests
let authToken = null;

// Function to handle login and store the token
async function loginUser(username, password) {
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${getBackendURL()}/users/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            chrome.storage.local.set({ authToken });
            console.log('Login successful, token stored.');
            return { success: true };
        } else {
            throw new Error('Login failed');
        }
    } catch (error) {
        console.error('Error logging in:', error);
        return { success: false, error: error.message };
    }
}

// Check if the user is already logged in
function checkLoginStatus() {
    return new Promise((resolve) => {
        chrome.storage.local.get('authToken', (result) => {
            authToken = result.authToken || null;
            resolve(!!authToken);
        });
    });
}

// Function to submit an article using the API
async function submitArticle(articleData) {
    if (!authToken) {
        console.error('User is not authenticated.');
        return { success: false, error: 'User is not authenticated' };
    }

    try {
        const response = await fetch(`${getBackendURL()}/api/articles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify(articleData)
        });

        // Try parsing the response body if the response is in JSON format
        let responseBody = null;
        try {
            responseBody = await response.json();  // Parse response as JSON
        } catch (error) {
            console.error('Error parsing JSON:', error);  // Catch parsing errors
        }

        if (response.ok) {
            console.log('Article submitted successfully:', responseBody);
            return { success: true };
        } else {
            console.error('Error submitting article:', responseBody);
            return { success: false, error: responseBody };
        }
    } catch (error) {
        console.error('Error submitting article:', error);
        return { success: false, error: error.message };
    }
}

// Listen for messages from popup.js or content.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'login') {
        loginUser(request.username, request.password).then(sendResponse);
        return true; // Keep the messaging channel open for async response
    }

    if (request.action === 'checkLoginStatus') {
        checkLoginStatus().then(sendResponse);
        return true;
    }

    if (request.action === 'submitArticle') {
        submitArticle(request.articleData).then(sendResponse);
        return true;
    }

    if (request.action === 'logout') {
        logoutUser().then(sendResponse);  // Handle logout
        return true;
    }
});
