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


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "extractArticle") {
        const articleContent = extractNYTArticle(request.tabUrl);  // Pass the tab URL
        if (articleContent) {
            sendResponse(articleContent);
        } else {
            sendResponse({ error: "Article content not found." });
        }
    }
    return true;
});
