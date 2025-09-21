document.addEventListener('DOMContentLoaded', async function() {
    const completedSessionsList = document.getElementById('completed-sessions-list');

    async function loadCompletedSessions() {
        const response = await fetchData('/api/completed_sessions');
        if (response.success) {
            completedSessionsList.innerHTML = '';
            if (response.sessions.length === 0) {
                completedSessionsList.innerHTML = '<p>No completed sessions yet.</p>';
            } else {
                response.sessions.forEach(s => {
                    completedSessionsList.innerHTML += `
                        <div class="session-card">
                            <h4>${s.class_name} - ${s.batch_name} (Session ${s.session_number})</h4>
                            <p>Date: ${new Date(s.start_time).toLocaleDateString()}</p>
                            <p>Status: ${s.status}</p>
                        </div>
                    `;
                });
            }
        }
    }
    loadCompletedSessions();
});