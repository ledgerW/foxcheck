document.addEventListener('DOMContentLoaded', () => {
    const articleId = window.location.pathname.split('/').pop();
    const loadingSpinner = document.querySelector('.loading-spinner');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mainContent = document.getElementById('main-content');
    let sidebarOpen = true;

    // Sidebar toggle functionality
    sidebarToggle.addEventListener('click', () => {
        sidebarOpen = !sidebarOpen;
        sidebar.classList.toggle('open', sidebarOpen);
        sidebarToggle.classList.toggle('open', sidebarOpen);
        mainContent.classList.toggle('sidebar-open', sidebarOpen);
        sidebarToggle.innerHTML = sidebarOpen ? 
            '<i class="bi bi-chevron-right"></i>' : 
            '<i class="bi bi-chevron-left"></i>';
    });

    function formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString(undefined, options);
    }

    async function loadArticle() {
        try {
            loadingSpinner.style.display = 'block';
            const response = await fetch(`/api/articles/${articleId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Article not found');
                }
                throw new Error('Failed to load article');
            }

            const article = await response.json();
            displayArticle(article);

            // Trigger sidebar open by default
            sidebar.classList.add('open');
            sidebarToggle.classList.add('open');
            mainContent.classList.add('sidebar-open');
            sidebarToggle.innerHTML = '<i class="bi bi-chevron-right"></i>';
        } catch (error) {
            console.error('Error loading article:', error);
            displayError(error.message);
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    function toggleStatement(statementId) {
        const content = document.getElementById(`statement-content-${statementId}`);
        const icon = document.getElementById(`statement-icon-${statementId}`);
        const isExpanded = content.classList.contains('expanded');
        
        content.classList.toggle('expanded');
        icon.classList.toggle('bi-chevron-down');
        icon.classList.toggle('bi-chevron-right');
    }

    function displayArticle(article) {
        document.title = `${article.title} - Statement Checker`;
        document.getElementById('article-title').textContent = article.title;
        
        // Display metadata
        const authorText = article.authors ? `By ${article.authors}` : '';
        const dateText = article.date ? ` • ${formatDate(article.date)}` : '';
        const domainText = article.domain ? ` • Source: ${article.domain}` : '';
        
        document.getElementById('article-author').textContent = authorText;
        document.getElementById('article-date').textContent = dateText;
        document.getElementById('article-domain').textContent = domainText;
        
        // Display content
        document.getElementById('article-content').textContent = article.text;
        
        // Display statements with their associated references
        const statementsContainer = document.getElementById('statements-container');
        if (article.statements && article.statements.length > 0) {
            const statementsHtml = article.statements.map((statement, index) => {
                // Find references associated with this statement
                const statementRefs = article.references.filter(ref => ref.statement_id === statement.id);
                
                return `
                    <div class="statement-card">
                        <div class="statement-header" onclick="toggleStatement(${index})">
                            <span class="statement-text">${statement.content}</span>
                            <i id="statement-icon-${index}" class="bi bi-chevron-right"></i>
                        </div>
                        <div id="statement-content-${index}" class="statement-content">
                            ${statement.verdict ? `
                                <div class="verdict mb-3">
                                    <strong>Verdict:</strong> ${statement.verdict}
                                </div>
                            ` : ''}
                            ${statement.explanation ? `
                                <div class="explanation mb-3">
                                    <strong>Explanation:</strong> ${statement.explanation}
                                </div>
                            ` : ''}
                            ${statementRefs.length > 0 ? `
                                <div class="statement-references">
                                    <h5>References</h5>
                                    ${statementRefs.map(reference => `
                                        <div class="reference-item">
                                            <h6 class="mb-2">
                                                <a href="${reference.url}" target="_blank" class="text-primary">
                                                    ${reference.title || reference.url}
                                                </a>
                                            </h6>
                                            ${reference.content ? `
                                                <p class="mb-2">${reference.content}</p>
                                            ` : ''}
                                            ${reference.context ? `
                                                <p class="text-muted mb-0"><small>${reference.context}</small></p>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            statementsContainer.innerHTML = statementsHtml;
        } else {
            statementsContainer.innerHTML = '<p>No statements available for this article.</p>';
        }

        // Make toggleStatement function globally available
        window.toggleStatement = toggleStatement;
    }

    function displayError(message) {
        const articleContainer = document.querySelector('.article-container');
        articleContainer.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">Error</h4>
                <p>${message}</p>
                <hr>
                <p class="mb-0">
                    <a href="/articles" class="alert-link">Return to articles list</a>
                </p>
            </div>
        `;
    }

    loadArticle();
});
