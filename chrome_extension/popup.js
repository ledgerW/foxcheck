document.addEventListener('DOMContentLoaded', () => {
    const extractButton = document.getElementById('extractButton');
    const loginStatus = document.getElementById('loginStatus');
    const loginForm = document.getElementById('loginForm');
    const logoutButton = document.getElementById('logoutButton');
    let loggedIn = false;

    // Check login status on popup load
    console.log('Checking login status...');
    chrome.runtime.sendMessage({ action: 'checkLoginStatus' }, (isLoggedIn) => {
        if (chrome.runtime.lastError) {
            console.error('Error checking login status:', chrome.runtime.lastError);
        } else {
            loggedIn = isLoggedIn;
            console.log('Login status:', loggedIn);

            if (loggedIn) {
                loginStatus.textContent = 'Logged in';
                extractButton.disabled = false;
                loginForm.style.display = 'none';  // Hide login form
                logoutButton.style.display = 'block';  // Show logout button
            } else {
                loginStatus.textContent = 'Please log in';
                extractButton.disabled = true;
                loginForm.style.display = 'block';  // Show login form
                logoutButton.style.display = 'none';  // Hide logout button
            }
        }
    });

    // Login handler
    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        
        // Retrieve values from the form
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        console.log('Username:', username);

        // Send login message to background.js
        chrome.runtime.sendMessage({ action: 'login', username, password }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error during login:', chrome.runtime.lastError);
                loginStatus.textContent = 'Login failed';
            } else if (response.success) {
                console.log('Login successful:', response);
                loginStatus.textContent = 'Logged in';
                extractButton.disabled = false;
                loginForm.style.display = 'none';  // Hide login form after success
                logoutButton.style.display = 'block';  // Show logout button after login
            } else {
                console.error('Login failed:', response.error);
                loginStatus.textContent = 'Login failed: ' + response.error;
            }
        });
    });

    // Log out handler
    logoutButton.addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'logout' }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error during logout:', chrome.runtime.lastError);
            } else {
                console.log('Logged out:', response);
                loginStatus.textContent = 'Please log in';
                extractButton.disabled = true;
                loginForm.style.display = 'block';  // Show login form
                logoutButton.style.display = 'none';  // Hide logout button
            }
        });
    });

    // Article extraction and submission
    extractButton.addEventListener('click', () => {
        console.log('Extracting article...');
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const tabUrl = tabs[0].url; // Get the URL of the active tab

            chrome.tabs.sendMessage(tabs[0].id, { action: 'extractArticle', tabUrl }, (articleContent) => {
                if (chrome.runtime.lastError) {
                    console.error('Error extracting article:', chrome.runtime.lastError);
                    alert('Error extracting article');
                } else if (articleContent) {
                    console.log('Article extracted:', articleContent);

                    // Display the article info in the popup
                    document.getElementById('articleTitle').textContent = articleContent.title;
                    document.getElementById('articleAuthors').textContent = articleContent.authors;
                    document.getElementById('publicationDate').textContent = articleContent.publicationDate;
                    document.getElementById('extractionDate').textContent = articleContent.currentDate;
                    document.getElementById('articleText').textContent = articleContent.text;

                    // Submit article to the API
                    console.log('Submitting article...');
                    chrome.runtime.sendMessage({
                        action: 'submitArticle',
                        articleData: {
                            domain: articleContent.domain,
                            title: articleContent.title,
                            text: articleContent.text,
                            authors: articleContent.authors,
                            publication_date: articleContent.publicationDate,
                            links: articleContent.links
                        }
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Error submitting article:', chrome.runtime.lastError);
                        } else if (response.success) {
                            console.log('Article submitted successfully');
                        } else {
                            console.error('Error submitting article:', response.error);
                        }
                    });
                } else {
                    console.error('No article content found.');
                }
            });
        });
    });
});
