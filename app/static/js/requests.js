document.addEventListener('DOMContentLoaded', () => {
    const requestsContainer = document.getElementById('requests-container');

    if (!requestsContainer) return;

    async function handleRequestAction(requestId, action) {
        try {
            const response = await fetch(`/api/mentor/request/${requestId}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                const requestCard = document.getElementById(`request-${requestId}`);
                if (requestCard) {
                    requestCard.style.transition = 'opacity 0.5s ease';
                    requestCard.style.opacity = '0';
                    setTimeout(() => {
                        requestCard.remove();
                        if (!requestsContainer.querySelector('.request-card')) {
                            requestsContainer.innerHTML = '<p>You have no pending absence requests.</p>';
                        }
                    }, 500);
                }
                // Optionally show a small success toast/notification here
            } else {
                throw new Error(result.message || 'An unknown error occurred.');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    requestsContainer.addEventListener('click', (e) => {
        const approveButton = e.target.closest('.btn-approve');
        const declineButton = e.target.closest('.btn-decline');

        if (approveButton) {
            const requestId = approveButton.dataset.requestId;
            if (confirm('Are you sure you want to approve this absence request?')) {
                handleRequestAction(requestId, 'approve');
            }
        }

        if (declineButton) {
            const requestId = declineButton.dataset.requestId;
            if (confirm('Are you sure you want to decline this absence request?')) {
                handleRequestAction(requestId, 'decline');
            }
        }
    });
});