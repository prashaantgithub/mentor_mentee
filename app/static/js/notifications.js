document.addEventListener('DOMContentLoaded', () => {
    const bell = document.getElementById('notification-bell');
    const count = document.getElementById('notification-count');
    const dropdown = document.getElementById('notification-dropdown');
    const list = document.getElementById('notification-list');

    const fetchNotifications = async () => {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            if (data.success) {
                list.innerHTML = '';
                if (data.notifications.length === 0) {
                    list.innerHTML = '<li>No new notifications</li>';
                } else {
                    data.notifications.forEach(n => {
                        const li = document.createElement('li');
                        if (!n.is_seen) li.classList.add('unseen');
                        li.innerHTML = `${n.message} <span class="timestamp">${new Date(n.timestamp).toLocaleString()}</span>`;
                        list.appendChild(li);
                    });
                }
                if (data.unseen_count > 0) {
                    count.textContent = data.unseen_count;
                    count.style.display = 'flex';
                } else {
                    count.style.display = 'none';
                }
            }
        } catch (error) { console.error("Could not fetch notifications:", error); }
    };

    if (bell) {
        bell.addEventListener('click', async (e) => {
            e.stopPropagation();
            const isActive = dropdown.classList.toggle('active');
            if (isActive && count.style.display !== 'none') {
                await fetch('/api/notifications/mark_as_read', { method: 'POST' });
                count.style.display = 'none';
            }
        });
    }

    document.addEventListener('click', () => {
        if (dropdown) dropdown.classList.remove('active');
    });
    if (dropdown) dropdown.addEventListener('click', e => e.stopPropagation());

    fetchNotifications();
    setInterval(fetchNotifications, 60000);
});