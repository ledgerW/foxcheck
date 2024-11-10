// Function to detect if we are in a DEV or PROD environment
function getBackendURL() {
    return "https://async-fast-api-chain-ledgerw.replit.app";
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
            //const data = await response.json();
            //console.log(data)
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
        console.log(articleData)
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


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getActiveTabInfo') {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                const tab = tabs[0];
                sendResponse({ success: true, url: tab.url, tabId: tab.id });
            } else {
                sendResponse({ success: false, error: 'No active tab found' });
            }
        });
        return true;  // Keep the message channel open for async response
    }

    if (request.action === 'login') {
        loginUser(request.username, request.password)
            .then((result) => sendResponse({ success: true, ...result }))
            .catch((error) => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (request.action === 'checkLoginStatus') {
        checkLoginStatus()
            .then((isLoggedIn) => sendResponse({ success: true, loggedIn: isLoggedIn }))
            .catch((error) => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (request.action === 'submitArticle') {
        submitArticle(request.articleData)
            .then((result) => sendResponse({ success: true, ...result }))
            .catch((error) => sendResponse({ success: false, error: error.message }));
        return true;
    }

    if (request.action === 'logout') {
        logoutUser()
            .then((result) => sendResponse({ success: true, ...result }))
            .catch((error) => sendResponse({ success: false, error: error.message }));
        return true;
    }
});




chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.sendMessage(tab.id, { action: 'toggleSidebar' });
});


