// content.js
function extractNYTArticle(tabUrl) {
    // Select the article body
    const articleElements = document.querySelectorAll('section[name="articleBody"] p');
    const linkElements = document.querySelectorAll('section[name="articleBody"] a');

    // Extract article's authors
    const authorElements = document.querySelectorAll('meta[name="byl"]');
    let authors = '';
    if (authorElements.length > 0) {
        authors = authorElements[0].getAttribute('content').replace('By ', '');
    }

    // Extract publication date
    const dateElement = document.querySelector('meta[property="article:published_time"]');
    let publicationDate = '';
    if (dateElement) {
        publicationDate = new Date(dateElement.getAttribute('content')).toLocaleDateString();
    }

    // Extract current date (date of extraction)
    const currentDate = new Date().toLocaleDateString();

    // Extract article text
    let articleText = '';
    articleElements.forEach(paragraph => {
        articleText += paragraph.innerText + "\n\n";
    });

    // Extract URLs from anchor tags within the article body
    let articleLinks = [];
    linkElements.forEach(link => {
        if (link.href && link.closest('section[name="articleBody"]')) {
            articleLinks.push(link.href);
        }
    });

    // Extract title from the <title> tag in the head or a meta tag
    let title = document.querySelector('meta[property="og:title"]');
    if (title) {
        title = title.getAttribute('content');
    } else {
        title = document.title || "No title found";
    }

    return {
        text: articleText,
        links: articleLinks,
        authors: authors,
        publication_date: publicationDate,
        currentDate: currentDate,
        title: title,
        domain: tabUrl  // Add the tab URL to the returned data
    };
}

function extractSubstackArticle(tabUrl) {
    // Select the article body
    const articleElements = document.querySelectorAll('div[class*="post-content"] p');
    const linkElements = document.querySelectorAll('div[class*="post-content"] a');

    // Extract the author's name
    const authorElement = document.querySelector('meta[name="author"]');
    let authors = '';
    if (authorElement) {
        authors = authorElement.getAttribute('content');
    }

    // Extract publication date
    const dateElement = document.querySelector('meta[property="article:published_time"]');
    let publicationDate = '';
    if (dateElement) {
        publicationDate = new Date(dateElement.getAttribute('content')).toLocaleDateString();
    }

    // Extract current date (date of extraction)
    const currentDate = new Date().toLocaleDateString();

    // Extract article text
    let articleText = '';
    articleElements.forEach(paragraph => {
        articleText += paragraph.innerText + "\n\n";
    });

    // Extract URLs from anchor tags within the article body
    let articleLinks = [];
    linkElements.forEach(link => {
        if (link.href) {
            articleLinks.push(link.href);
        }
    });

    // Extract title from the <title> tag in the head or a meta tag
    let titleElement = document.querySelector('meta[property="og:title"]');
    let title = titleElement ? titleElement.getAttribute('content') : document.title || "No title found";

    return {
        text: articleText,
        links: articleLinks,
        authors: authors,
        publication_date: publicationDate,
        currentDate: currentDate,
        title: title,
        domain: tabUrl  // Include the URL of the Substack article
    };
}

const sidebarCSS = `
    #sidebar {
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100%;
        background-color: #f9f9f9;
        box-shadow: -3px 0 5px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        font-family: Arial, sans-serif;
        padding: 20px;
    }
    #sidebar.open {
        transform: translateX(0);
    }
    #closeSidebar {
        padding: 10px;
        font-size: 18px;
        text-align: right;
        cursor: pointer;
        color: #333;
    }
    #sidebar h2 {
        text-align: center;
        color: #333;
        margin-bottom: 20px;
    }
    #extractButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 18px;
        cursor: pointer;
        border-radius: 8px;
        display: block;
        margin: 20px auto;
        transition: background-color 0.3s ease;
    }
    #extractButton:hover {
        background-color: #45a049;
    }
    #contentContainer {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 20px;
        margin-top: 20px;
    }
    .infoContainer {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
    }
    .infoContainer h3 {
        margin-bottom: 5px;
    }
    .infoContainer p {
        margin: 0;
        font-size: 16px;
        color: #555;
    }
    #articleText, #articleLinks {
        background-color: #fff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        max-height: 300px;
        overflow-y: auto;
    }
    #articleText {
        white-space: pre-wrap;
    }
    #articleLinks a {
        color: #4CAF50;
        text-decoration: none;
    }
    #articleLinks a:hover {
        text-decoration: underline;
    }
    #loginStatus {
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    #loginForm {
        display: none;
        margin-top: 20px;
    }
    #loginForm label {
        display: block;
        margin-bottom: 10px;
        font-size: 16px;
    }
    #loginForm input {
        width: calc(100% - 20px);
        padding: 12px 10px;
        margin-bottom: 20px;
        border-radius: 5px;
        border: 1px solid #ccc;
        font-size: 16px;
    }
    #loginForm button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 12px 20px;
        font-size: 16px;
        cursor: pointer;
        border-radius: 5px;
        display: block;
        margin: 0 auto;
    }
    #loginForm button:hover {
        background-color: #45a049;
    }
    #logoutButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 15px 30px;
        font-size: 18px;
        cursor: pointer;
        border-radius: 8px;
        display: block;
        margin: 20px auto;
        transition: background-color 0.3s ease;
    }
    #logoutButton:hover {
        background-color: #45a049;
    }
`;


const sidebarHTML = `
    <div id="sidebar">
        <div id="closeSidebar">× Close</div>
        <h2>Article Extractor</h2>

        <!-- Display login status -->
        <p id="loginStatus">Checking login status...</p>

        <!-- Login Form -->
        <form id="loginForm">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" placeholder="Enter your username" required>
            
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" placeholder="Enter your password" required>
            
            <button type="submit">Login</button>
        </form>
        

        <button id="extractButton" disabled>Extract Article</button>

        <button id="logoutButton" style="display: none;">Log Out</button>


        
    </div>
`;


// Inject Sidebar HTML and CSS if not already present
if (!document.getElementById('sidebar')) {
    document.body.insertAdjacentHTML('beforeend', `<style>${sidebarCSS}</style>${sidebarHTML}`);
    document.getElementById('closeSidebar').addEventListener('click', closeSidebar);
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('open');
}

const extractButton = document.getElementById('extractButton');
const loginStatus = document.getElementById('loginStatus');
const loginForm = document.getElementById('loginForm');
const logoutButton = document.getElementById('logoutButton');
let loggedIn = false;

// Check login status on sidebar load
chrome.runtime.sendMessage({ action: 'checkLoginStatus' }, (response) => {
    if (chrome.runtime.lastError) {
        console.error('Error checking login status:', chrome.runtime.lastError);
        loginStatus.textContent = 'Error checking login status';
    } else if (response && response.success) {
        loggedIn = response.loggedIn;
        loginStatus.textContent = loggedIn ? 'Logged in' : 'Please log in';
        extractButton.disabled = !loggedIn;
        loginForm.style.display = loggedIn ? 'none' : 'block';
        logoutButton.style.display = loggedIn ? 'block' : 'none';
    } else {
        loginStatus.textContent = 'Login status check failed';
    }
});

// Login handler
loginForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    chrome.runtime.sendMessage({ action: 'login', username, password }, (response) => {
        if (chrome.runtime.lastError) {
            loginStatus.textContent = 'Login failed';
        } else if (response.success) {
            loginStatus.textContent = 'Logged in';
            extractButton.disabled = false;
            loginForm.style.display = 'none';
            logoutButton.style.display = 'block';
        } else {
            loginStatus.textContent = 'Login failed: ' + response.error;
        }
    });
});

// Logout handler
logoutButton.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'logout' }, (response) => {
        if (chrome.runtime.lastError) {
            console.error('Error during logout:', chrome.runtime.lastError);
        } else {
            loginStatus.textContent = 'Please log in';
            extractButton.disabled = true;
            loginForm.style.display = 'block';
            logoutButton.style.display = 'none';
        }
    });
});

// Article extraction and submission
extractButton.addEventListener('click', () => {
    // Request the active tab's URL and ID from background.js
    chrome.runtime.sendMessage({ action: 'getActiveTabInfo' }, (response) => {
        if (chrome.runtime.lastError || !response.success) {
            console.error('Error retrieving active tab info:', chrome.runtime.lastError || response.error);
            alert('Error retrieving active tab info');
            return;
        }

        const tabId = response.tabId;
        const tabUrl = response.url;

        // Check if tabId and tabUrl are defined before proceeding
        if (!tabId || !tabUrl) {
            console.error('tabId or tabUrl is undefined. Cannot proceed with article extraction.');
            return;
        }

        console.log(`Sending extractArticle message to tabId ${tabId} with URL ${tabUrl}`);

        // Extract Article Content
        let articleContent;
        if (tabUrl.includes("nytimes.com")) {
            console.log('Extracting NTY Article')
            articleContent = extractNYTArticle(tabUrl);
        } else {
            console.log('Extracting Substack Article')
            articleContent = extractSubstackArticle(tabUrl);
        }
        console.log("Article Content: ", articleContent)
        
        if (articleContent) {
            // Submit the article to the backend
            chrome.runtime.sendMessage({
                action: 'submitArticle',
                articleData: {
                    domain: articleContent.domain,
                    title: articleContent.title,
                    text: articleContent.text,
                    authors: articleContent.authors,
                    publication_date: articleContent.publication_date,
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


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggleSidebar') {
        toggleSidebar();
    }

    return true;  // Keeps the message channel open for asynchronous response
});
