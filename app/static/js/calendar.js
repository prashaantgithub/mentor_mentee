document.addEventListener('DOMContentLoaded', () => {
    const calendarDaysContainer = document.getElementById('calendar-days');
    const currentMonthYearDisplay = document.getElementById('current-month-year');
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    const meetingsListBody = document.getElementById('meetings-list');
    const meetingProposalForm = document.getElementById('meeting-proposal-form');
    const menteeSelect = document.getElementById('mentee_id'); // For mentor's proposal form

    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();

    // Helper to get user role from a global JS variable (set by Flask in base.html)
    const userRole = document.body.dataset.userRole; // Assume Flask sets <body data-user-role="{{ current_user.role }}">

    async function fetchMeetingsForMonth(year, month) {
        try {
            // Month is 0-indexed in JS, but API might expect 1-indexed
            const response = await getData(`/api/meetings?year=${year}&month=${month + 1}`);
            if (response.success) {
                return response.meetings;
            } else {
                showMessage('error', response.message || 'Failed to fetch meetings.');
                return [];
            }
        } catch (error) {
            console.error('Error fetching meetings:', error);
            showMessage('error', 'An error occurred while fetching meetings.');
            return [];
        }
    }

    async function renderCalendar() {
        calendarDaysContainer.innerHTML = '';
        const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
        const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);
        const numDaysInMonth = lastDayOfMonth.getDate();

        // Get the day of the week for the first day (0 = Sunday, 6 = Saturday)
        const startDayOfWeek = firstDayOfMonth.getDay();

        // Update month/year display
        currentMonthYearDisplay.textContent = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(firstDayOfMonth);

        // Fetch meetings for the current month
        const meetings = await fetchMeetingsForMonth(currentYear, currentMonth);

        // Fill leading empty days
        for (let i = 0; i < startDayOfWeek; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.classList.add('calendar-day', 'inactive');
            calendarDaysContainer.appendChild(emptyDay);
        }

        // Fill days of the month
        for (let day = 1; day <= numDaysInMonth; day++) {
            const dayDiv = document.createElement('div');
            dayDiv.classList.add('calendar-day');
            dayDiv.innerHTML = `<span class="calendar-date">${day}</span>`;

            // Add events for this day
            const dayMeetings = meetings.filter(meeting => {
                const meetingDate = new Date(meeting.date_time);
                return meetingDate.getDate() === day &&
                       meetingDate.getMonth() === currentMonth &&
                       meetingDate.getFullYear() === currentYear;
            });

            dayMeetings.forEach(meeting => {
                const eventDiv = document.createElement('div');
                eventDiv.classList.add('calendar-event');
                eventDiv.dataset.meetingId = meeting.id;
                eventDiv.innerHTML = `
                    ${meeting.title} - ${new Date(meeting.date_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    <br> <small>${meeting.status}</small>
                `;
                eventDiv.addEventListener('click', () => showMeetingDetails(meeting));
                dayDiv.appendChild(eventDiv);
            });

            calendarDaysContainer.appendChild(dayDiv);
        }

        // Fill trailing empty days (to complete the last week row if needed)
        const totalCells = startDayOfWeek + numDaysInMonth;
        const remainingCells = 42 - totalCells; // Max 6 rows * 7 days = 42 cells
        for (let i = 0; i < remainingCells && (totalCells + i) % 7 !== 0; i++) {
             const emptyDay = document.createElement('div');
             emptyDay.classList.add('calendar-day', 'inactive');
             calendarDaysContainer.appendChild(emptyDay);
        }

        renderMeetingsList(meetings);
    }

    function showMeetingDetails(meeting) {
        let detailsHtml = `
            <h3>${meeting.title}</h3>
            <p><strong>With:</strong> ${meeting.participant_name}</p>
            <p><strong>Date & Time:</strong> ${new Date(meeting.date_time).toLocaleString()}</p>
            <p><strong>Duration:</strong> ${meeting.duration} minutes</p>
            <p><strong>Type:</strong> ${meeting.type}</p>
            <p><strong>Status:</strong> <span class="badge status-${meeting.status.toLowerCase()}">${meeting.status}</span></p>
            <p><strong>Notes:</strong> ${meeting.notes || 'N/A'}</p>
        `;

        if (userRole === 'mentee' && meeting.status === 'Pending') {
            detailsHtml += `
                <div class="meeting-response-section">
                    <h4>Respond to Meeting:</h4>
                    <form id="meeting-response-form" data-meeting-id="${meeting.id}">
                        <div class="form-group">
                            <label><input type="radio" name="action" value="accept" required> Accept</label>
                            <label><input type="radio" name="action" value="reject"> Reject</label>
                            <label><input type="radio" name="action" value="reschedule"> Suggest Reschedule</label>
                        </div>
                        <div class="form-group reschedule-options" style="display: none;">
                            <label for="new_date">New Date:</label>
                            <input type="date" id="new_date" name="new_date">
                            <label for="new_time">New Time:</label>
                            <input type="time" id="new_time" name="new_time">
                        </div>
                        <div class="form-group">
                            <label for="reason">Reason (if rejecting/rescheduling):</label>
                            <textarea id="reason" name="reason" placeholder="Optional reason..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Submit Response</button>
                    </form>
                </div>
            `;
        } else if (userRole === 'mentor' && meeting.status === 'Reschedule Proposed') {
             detailsHtml += `
                <div class="meeting-response-section">
                    <h4>Respond to Reschedule Request:</h4>
                    <p>Mentee suggested: ${new Date(meeting.proposed_reschedule_datetime).toLocaleString()} with reason: "${meeting.reschedule_reason || 'N/A'}"</p>
                    <form id="reschedule-mentor-response-form" data-meeting-id="${meeting.id}">
                        <div class="form-group">
                            <label><input type="radio" name="action" value="approve" required> Approve Reschedule</label>
                            <label><input type="radio" name="action" value="reject"> Reject Reschedule</label>
                        </div>
                        <div class="form-group">
                            <label for="mentor_response_message">Message to Mentee:</label>
                            <textarea id="mentor_response_message" name="mentor_response_message" placeholder="Optional message..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Send Response</button>
                    </form>
                </div>
            `;
        }

        // A simple modal/dialog system
        const dialog = document.createElement('div');
        dialog.className = 'modal-overlay';
        dialog.innerHTML = `
            <div class="modal-content card">
                <span class="close-button">×</span>
                ${detailsHtml}
            </div>
        `;
        document.body.appendChild(dialog);

        dialog.querySelector('.close-button').addEventListener('click', () => dialog.remove());
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) dialog.remove();
        });

        const rescheduleOptions = dialog.querySelector('.reschedule-options');
        if (rescheduleOptions) {
            dialog.querySelectorAll('input[name="action"]').forEach(radio => {
                radio.addEventListener('change', (e) => {
                    if (e.target.value === 'reschedule') {
                        rescheduleOptions.style.display = 'block';
                    } else {
                        rescheduleOptions.style.display = 'none';
                    }
                });
            });

            // Handle mentee response form submission
            const menteeResponseForm = dialog.querySelector('#meeting-response-form');
            if (menteeResponseForm) {
                menteeResponseForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData(menteeResponseForm);
                    const responseData = Object.fromEntries(formData.entries());
                    const meetingId = menteeResponseForm.dataset.meetingId;

                    if (responseData.action === 'reschedule' && (!responseData.new_date || !responseData.new_time)) {
                        showMessage('error', 'Please provide a new date and time for reschedule.');
                        return;
                    }

                    try {
                        const response = await postData(`/api/mentee/meetings/${meetingId}/respond`, responseData);
                        if (response.success) {
                            showMessage('success', response.message);
                            dialog.remove();
                            renderCalendar(); // Re-render calendar to update status
                            renderMeetingsListForUser(); // Refresh detailed list
                        } else {
                            showMessage('error', response.message || 'Failed to send response.');
                        }
                    } catch (error) {
                        console.error('Error responding to meeting:', error);
                        showMessage('error', 'An unexpected error occurred.');
                    }
                });
            }
        }

        // Handle mentor response to reschedule request
        const mentorResponseForm = dialog.querySelector('#reschedule-mentor-response-form');
        if (mentorResponseForm) {
            mentorResponseForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(mentorResponseForm);
                const responseData = Object.fromEntries(formData.entries());
                const meetingId = mentorResponseForm.dataset.meetingId;

                try {
                    const response = await postData(`/api/mentor/meetings/${meetingId}/respond_reschedule`, responseData);
                    if (response.success) {
                        showMessage('success', response.message);
                        dialog.remove();
                        renderCalendar();
                        renderMeetingsListForUser();
                    } else {
                        showMessage('error', response.message || 'Failed to process reschedule response.');
                    }
                } catch (error) {
                    console.error('Error responding to reschedule:', error);
                    showMessage('error', 'An unexpected error occurred.');
                }
            });
        }
    }


    async function renderMeetingsList(meetings) {
        if (!meetingsListBody) return;
        meetingsListBody.innerHTML = ''; // Clear previous list

        if (meetings.length === 0) {
            meetingsListBody.innerHTML = '<tr><td colspan="5">No meetings found for this month.</td></tr>';
            return;
        }

        meetings.sort((a, b) => new Date(a.date_time) - new Date(b.date_time));

        meetings.forEach(meeting => {
            const row = document.createElement('tr');
            const participantName = userRole === 'mentor' ? meeting.mentee_name : meeting.mentor_name;
            const meetingTime = new Date(meeting.date_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });

            let actionsHtml = `<button class="btn btn-secondary btn-sm" data-action="view" data-meeting-id="${meeting.id}">View</button>`;
            if (userRole === 'mentor') {
                actionsHtml += `<button class="btn btn-danger btn-sm" data-action="cancel" data-meeting-id="${meeting.id}">Cancel</button>`;
            } else if (userRole === 'mentee') {
                 if (meeting.status === 'Confirmed' || meeting.status === 'Pending') { // Can reschedule if confirmed or pending response
                    actionsHtml += `<button class="btn btn-warning btn-sm" data-action="reschedule" data-meeting-id="${meeting.id}">Reschedule</button>`;
                }
            }


            row.innerHTML = `
                <td>${participantName}</td>
                <td>${meetingTime}</td>
                <td><span class="badge status-type">${meeting.type}</span></td>
                <td><span class="badge status-${meeting.status.toLowerCase().replace(/\s/g, '-') || 'info'}">${meeting.status}</span></td>
                <td>${actionsHtml}</td>
            `;
            meetingsListBody.appendChild(row);
        });

        meetingsListBody.querySelectorAll('button[data-action="view"]').forEach(button => {
            button.addEventListener('click', async (e) => {
                const meetingId = e.target.dataset.meetingId;
                const meeting = meetings.find(m => m.id == meetingId); // Find the full meeting object
                if (meeting) {
                    showMeetingDetails(meeting);
                }
            });
        });

        meetingsListBody.querySelectorAll('button[data-action="cancel"]').forEach(button => {
            button.addEventListener('click', async (e) => {
                const meetingId = e.target.dataset.meetingId;
                if (confirm('Are you sure you want to cancel this meeting?')) {
                    try {
                        const response = await postData(`/api/mentor/meetings/${meetingId}/cancel`, {});
                        if (response.success) {
                            showMessage('success', response.message);
                            renderCalendar();
                            renderMeetingsListForUser();
                        } else {
                            showMessage('error', response.message || 'Failed to cancel meeting.');
                        }
                    } catch (error) {
                        console.error('Error canceling meeting:', error);
                        showMessage('error', 'An error occurred.');
                    }
                }
            });
        });

        meetingsListBody.querySelectorAll('button[data-action="reschedule"]').forEach(button => {
            button.addEventListener('click', async (e) => {
                const meetingId = e.target.dataset.meetingId;
                const meetingToReschedule = meetings.find(m => m.id == meetingId);
                if (meetingToReschedule) {
                     // Simulate showing reschedule form in a modal or inline
                     showMeetingDetails(meetingToReschedule); // Re-use the modal to handle reschedule response logic
                }
            });
        });
    }

    // This function can be used to render all user's meetings without month filter
    async function renderMeetingsListForUser() {
        if (!meetingsListBody) return;
        try {
            const url = userRole === 'mentor' ? '/api/mentor/meetings/all' : '/api/mentee/meetings/all';
            const response = await getData(url);
            if (response.success) {
                renderMeetingsList(response.meetings); // Reuse calendar list rendering for simplicity
            } else {
                showMessage('error', response.message || 'Failed to load all meetings.');
            }
        } catch (error) {
            console.error('Error fetching all meetings:', error);
            showMessage('error', 'An error occurred while fetching meetings.');
        }
    }


    // Event listeners for month navigation
    prevMonthBtn.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });

    // Mentee selection for mentor
    async function populateMenteeSelect() {
        if (menteeSelect && userRole === 'mentor') {
            try {
                const response = await getData('/api/mentor/my_mentees');
                if (response.success) {
                    menteeSelect.innerHTML = '<option value="">Select a mentee</option>';
                    response.mentees.forEach(mentee => {
                        const option = document.createElement('option');
                        option.value = mentee.id;
                        option.textContent = mentee.name;
                        menteeSelect.appendChild(option);
                    });
                } else {
                    showMessage('error', 'Failed to load mentees for proposal.');
                }
            } catch (error) {
                console.error('Error loading mentees:', error);
                showMessage('error', 'An error occurred while loading mentees.');
            }
        }
    }

    // Meeting proposal form submission for mentors
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
                    renderCalendar(); // Re-render calendar to show new proposed meetings
                    renderMeetingsListForUser(); // Refresh the full list
                } else {
                    showMessage('error', response.message || 'Failed to propose meeting.');
                }
            } catch (error) {
                console.error('Error proposing meeting:', error);
                showMessage('error', 'An unexpected error occurred.');
            }
        });
    }

    // Initial render when the page loads
    renderCalendar();
    renderMeetingsListForUser(); // Populate the detailed list as well
    populateMenteeSelect(); // If mentor, populate mentee dropdown
});