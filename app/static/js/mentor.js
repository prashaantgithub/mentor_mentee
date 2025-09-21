document.addEventListener('DOMContentLoaded', () => {
    const meetingProposalForm = document.getElementById('meeting-proposal-form');

    if (meetingProposalForm) {
        meetingProposalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(meetingProposalForm);
            const proposalData = Object.fromEntries(formData.entries());
            proposalData.recurring_day = parseInt(proposalData.recurring_day); // Ensure day is int

            try {
                const response = await postData('/api/mentor/propose_meeting', proposalData);
                if (response.success) {
                    showMessage('success', response.message);
                    meetingProposalForm.reset();
                    // Optionally refresh calendar or list of proposed meetings
                } else {
                    showMessage('error', response.message || 'Failed to propose meeting.');
                }
            } catch (error) {
                console.error('Error proposing meeting:', error);
                showMessage('error', 'An unexpected error occurred.');
            }
        });
    }

    // Example: Fetch and display mentees
    async function fetchMentees() {
        const menteesList = document.getElementById('mentees-list');
        if (!menteesList) return;

        try {
            const response = await getData('/api/mentor/my_mentees');
            if (response.success) {
                menteesList.innerHTML = '';
                if (response.mentees.length === 0) {
                    menteesList.innerHTML = '<p class="info-text">You currently have no mentees assigned.</p>';
                    return;
                }
                response.mentees.forEach(mentee => {
                    const menteeItem = document.createElement('div');
                    menteeItem.className = 'mentee-card card';
                    menteeItem.innerHTML = `
                        <img src="${mentee.profile_picture || 'https://via.placeholder.com/100'}" alt="Profile Picture" class="profile-picture">
                        <h3>${mentee.name}</h3>
                        <p>Email: ${mentee.email}</p>
                        <p>Department: ${mentee.department}</p>
                        <p>GPA: ${mentee.gpa ? mentee.gpa.toFixed(2) : 'N/A'}</p>
                        <div class="mentee-actions">
                            <a href="/profile/${mentee.id}" class="btn btn-secondary btn-sm">View Profile</a>
                            <a href="/chat/${mentee.id}" class="btn btn-primary btn-sm">Chat</a>
                        </div>
                    `;
                    menteesList.appendChild(menteeItem);
                });
            } else {
                showMessage('error', response.message || 'Failed to load mentees.');
            }
        } catch (error) {
            console.error('Error fetching mentees:', error);
            showMessage('error', 'An error occurred while fetching mentees.');
        }
    }

    if (document.body.classList.contains('page-mentor-mentees')) {
        fetchMentees();
    }
});