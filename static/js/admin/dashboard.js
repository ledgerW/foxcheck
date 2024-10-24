document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
});

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/admin/stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok) {
            const stats = await response.json();
            
            // Update stats cards
            document.getElementById('total-users').textContent = stats.users_count;
            document.getElementById('total-articles').textContent = stats.articles_count;
            document.getElementById('total-statements').textContent = stats.statements_count;
        } else {
            console.error('Failed to load dashboard stats');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}
