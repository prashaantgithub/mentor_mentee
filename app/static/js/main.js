document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const root = document.documentElement;

    const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : 'light';
    root.setAttribute('data-theme', currentTheme);
    if (currentTheme === 'dark') {
        themeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
    }

    themeToggle.addEventListener('click', () => {
        let theme = root.getAttribute('data-theme');
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            themeToggle.querySelector('i').classList.replace('fa-sun', 'fa-moon');
        } else {
            root.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            themeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
        }
    });

    const notificationBell = document.getElementById('notification-bell');
    const notificationDropdown = document.getElementById('notification-dropdown');

    if (notificationBell && notificationDropdown) {
        notificationBell.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationDropdown.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!notificationDropdown.contains(e.target) && !notificationBell.contains(e.target)) {
                notificationDropdown.classList.remove('active');
            }
        });
    }

    const sidebarLinks = document.querySelectorAll('.sidebar-nav a');
    const currentPath = window.location.pathname;
    let bestMatch = null;
    let longestMatchLength = 0;

    sidebarLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;

        if (currentPath.startsWith(linkPath)) {
            if (linkPath === '/' && currentPath !== '/') {
                return;
            }
            if (linkPath.length > longestMatchLength) {
                longestMatchLength = linkPath.length;
                bestMatch = link;
            }
        }
    });

    sidebarLinks.forEach(link => link.classList.remove('active'));

    if (bestMatch) {
        bestMatch.classList.add('active');
    }

    const appModalElement = document.getElementById('appModal');
    if (appModalElement) {
        const appModal = new bootstrap.Modal(appModalElement);
        const modalTitle = document.getElementById('appModalLabel');
        const modalBody = document.getElementById('appModalBody');

        document.addEventListener('click', async (event) => {
            const button = event.target.closest('.view-session-details-btn');
            if (!button) return;

            const sessionId = button.dataset.sessionId;
            if (!sessionId) return;

            modalTitle.textContent = 'Loading Session Details...';
            modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
            appModal.show();

            try {
                const data = await fetchData(`/api/session/${sessionId}/details`);

                if (data.success) {
                    const details = data.details;
                    modalTitle.textContent = 'Session Details';
                    modalBody.innerHTML = `
                        <p><strong>Meeting Time:</strong> ${details.meeting_time || 'N/A'}</p>
                        <p><strong>Mentor Name:</strong> ${details.mentor_name || 'N/A'}</p>
                        <p><strong>Cabin Details:</strong> ${details.cabin_details || 'N/A'}</p>
                    `;
                } else {
                    modalTitle.textContent = 'Error';
                    modalBody.textContent = data.message || 'Could not load session details.';
                }
            } catch (error) {
                console.error('Error fetching session details:', error);
                modalTitle.textContent = 'Error';
                modalBody.textContent = 'A network error occurred. Please try again.';
            }
        });
    }
});

async function fetchData(url, method = 'GET', data = null) {
    const options = { method: method, headers: {'Content-Type': 'application/json'} };
    if (data) options.body = JSON.stringify(data);
    const response = await fetch(url, options);
    return response.json();
}

function showAlert(message, type = 'success') {
    const container = document.querySelector('.main-content .container');
    if (!container) return;
    const alertDiv = document.createElement('div');
    alertDiv.className = `message ${type}`;
    alertDiv.textContent = message;
    container.prepend(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}