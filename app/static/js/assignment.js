document.addEventListener('DOMContentLoaded', () => {
    const batchListContainer = document.getElementById('batch-list-container');
    const mentorListContainer = document.getElementById('mentor-list-container');
    const assignAndScheduleBtn = document.getElementById('assign-and-schedule-btn');

    const scheduleModal = document.getElementById('schedule-modal');
    const closeScheduleModalBtn = document.getElementById('close-schedule-modal');
    const cancelScheduleBtn = document.getElementById('cancel-schedule-btn');
    const scheduleForm = document.getElementById('schedule-form');

    const reviewModal = document.getElementById('review-modal');
    const editScheduleBtn = document.getElementById('edit-schedule-btn');
    const confirmAssignmentBtn = document.getElementById('confirm-assignment-btn');

    const studentListModal = document.getElementById('student-list-modal');
    const studentListModalTitle = document.getElementById('student-list-modal-title');
    const studentListModalBody = document.getElementById('student-list-modal-body');

    let state = {
        selectedBatches: new Set(),
        selectedMentorId: null,
        scheduleData: {}
    };

    const fetchData = async (url) => {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Fetch error:", error);
            return null;
        }
    };

    const renderBatches = (data) => {
        if (!data || !data.success || data.batches.length === 0) {
            batchListContainer.innerHTML = '<p class="text-center">No unassigned batches available.</p>';
            return;
        }
        batchListContainer.innerHTML = data.batches.map(batch => `
            <div class="batch-button-group">
                <input type="checkbox" id="batch-${batch.id}" data-id="${batch.id}" data-name="${batch.name}">
                <label for="batch-${batch.id}">
                    <span>${batch.name}</span>
                    <a href="#" class="view-students-link" data-batch-id="${batch.id}" data-batch-name="${batch.name}" data-student-count="${batch.student_count}">
                        <span class="badge">${batch.student_count} Students</span>
                    </a>
                </label>
            </div>
        `).join('');
    };

    const renderMentors = (data) => {
        if (!data || !data.success || data.mentors.length === 0) {
            mentorListContainer.innerHTML = '<p class="text-center">No active mentors found.</p>';
            return;
        }
        mentorListContainer.innerHTML = data.mentors.map(mentor => `
            <div class="mentor-list-item">
                <input type="radio" id="mentor-${mentor.id}" name="mentor" data-id="${mentor.id}" data-name="${mentor.name}">
                <label for="mentor-${mentor.id}">${mentor.name}</label>
            </div>
        `).join('');
    };

    const checkButtonState = () => {
        assignAndScheduleBtn.disabled = !(state.selectedBatches.size > 0 && state.selectedMentorId);
    };

    const handleSelection = (e) => {
        if (e.target.type === 'checkbox') {
            const id = e.target.dataset.id;
            if (e.target.checked) {
                state.selectedBatches.add(id);
            } else {
                state.selectedBatches.delete(id);
            }
        }
        if (e.target.type === 'radio') {
            state.selectedMentorId = e.target.dataset.id;
        }
        checkButtonState();
    };


    const openModal = (modal) => modal.style.display = 'flex';
    const closeModal = (modal) => modal.style.display = 'none';

    const showReviewModal = () => {
        const batchNames = Array.from(state.selectedBatches).map(id => 
            document.querySelector(`#batch-${id}`).dataset.name
        );
        const mentorName = document.querySelector(`#mentor-${state.selectedMentorId}`).dataset.name;
        const dayOfWeekSelect = scheduleForm.elements['day-of-week'];
        const dayOfWeekText = dayOfWeekSelect.options[dayOfWeekSelect.selectedIndex].text;
        
        document.getElementById('review-batch-list').innerHTML = batchNames.map(name => `<li>${name}</li>`).join('');
        document.getElementById('review-mentor-name').textContent = mentorName;
        document.getElementById('review-schedule-summary').textContent = `Every ${dayOfWeekText} at ${state.scheduleData.time} for ${state.scheduleData.num_weeks} weeks, starting on ${state.scheduleData.start_date}.`;

        closeModal(scheduleModal);
        openModal(reviewModal);
    };
    
    const openStudentModal = async (batchId, batchName, studentCount) => {
        studentListModalTitle.textContent = `Students in ${batchName} (${studentCount} Students)`;
        studentListModalBody.innerHTML = '<p>Loading students...</p>';
        openModal(studentListModal);
        const data = await fetchData(`/api/admin/batch/${batchId}/students`);
        if (data && data.success) {
            if (data.students.length > 0) {
                const table = `
                    <table class="data-table">
                        <thead><tr><th>Name</th><th>Reg. No</th></tr></thead>
                        <tbody>${data.students.map(s => `<tr><td>${s.name}</td><td>${s.reg_num}</td></tr>`).join('')}</tbody>
                    </table>`;
                studentListModalBody.innerHTML = table;
            } else {
                studentListModalBody.innerHTML = '<p>No students found in this batch.</p>';
            }
        } else {
            studentListModalBody.innerHTML = '<p>Could not load students. Please try again.</p>';
        }
    };

    const finalAssignment = async () => {
        confirmAssignmentBtn.disabled = true;
        confirmAssignmentBtn.textContent = 'Assigning...';
        const payload = {
            mentor_id: state.selectedMentorId,
            batch_ids: Array.from(state.selectedBatches),
            schedule: state.scheduleData
        };
        const response = await fetch('/api/admin/assign_and_schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (result.success) {
            alert(result.message);
            window.location.reload();
        } else {
            if(result.collision){
                alert(`Error: ${result.message}`);
                closeModal(reviewModal);
            } else {
                alert(`An unexpected error occurred: ${result.message}`);
            }
            confirmAssignmentBtn.disabled = false;
            confirmAssignmentBtn.textContent = 'Confirm Assignment';
        }
    };

    batchListContainer.addEventListener('change', handleSelection);
    mentorListContainer.addEventListener('change', handleSelection);
    
    batchListContainer.addEventListener('click', (e) => {
        const link = e.target.closest('.view-students-link');
        if (link) {
            e.preventDefault();
            e.stopPropagation();
            const batchId = link.dataset.batchId;
            const batchName = link.dataset.batchName;
            const studentCount = link.dataset.studentCount;
            openStudentModal(batchId, batchName, studentCount);
        }
    });

    assignAndScheduleBtn.addEventListener('click', () => openModal(scheduleModal));
    closeScheduleModalBtn.addEventListener('click', () => closeModal(scheduleModal));
    cancelScheduleBtn.addEventListener('click', () => closeModal(scheduleModal));
    
    scheduleForm.addEventListener('submit', (e) => {
        e.preventDefault();
        state.scheduleData = {
            start_date: scheduleForm.elements['start-date'].value,
            day_of_week: scheduleForm.elements['day-of-week'].value,
            time: scheduleForm.elements['time'].value,
            num_weeks: scheduleForm.elements['num-weeks'].value
        };
        showReviewModal();
    });

    editScheduleBtn.addEventListener('click', () => {
        closeModal(reviewModal);
        openModal(scheduleModal);
    });

    confirmAssignmentBtn.addEventListener('click', finalAssignment);
    
    const init = async () => {
        renderBatches(await fetchData('/api/admin/unassigned_batches'));
        renderMentors(await fetchData('/api/admin/mentors'));
    };

    init();
});