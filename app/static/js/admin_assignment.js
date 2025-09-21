document.addEventListener('DOMContentLoaded', function() {
    const batchList = document.getElementById('batch-list');
    const mentorList = document.getElementById('mentor-list');
    const nextBtn = document.getElementById('next-btn');
    const scheduleModal = document.getElementById('schedule-modal');
    const reviewPage = document.getElementById('review-page');
    const scheduleForm = document.getElementById('schedule-form');

    let selectedBatches = [];
    let selectedMentor = null;
    let currentBatchIndex = 0;
    let scheduledData = [];

    async function loadAssignmentData() {
        const batchesRes = await fetchData('/api/admin/unassigned_batches');
        const mentorsRes = await fetchData('/api/admin/mentors');

        if (batchesRes.success) {
            batchList.innerHTML = batchesRes.batches.map(b => `<div class="user-item"><input type="checkbox" id="batch-${b.id}" value="${b.id}"><label for="batch-${b.id}">${b.name}</label></div>`).join('');
        }
        if (mentorsRes.success) {
            mentorList.innerHTML = mentorsRes.mentors.map(m => `<div class="user-item"><input type="radio" name="mentor_id" id="mentor-${m.id}" value="${m.id}"><label for="mentor-${m.id}">${m.name}</label></div>`).join('');
        }
        updateCounts();
    }

    function updateCounts() {
        document.getElementById('batch-count').textContent = `(${batchList.querySelectorAll('input:checked').length})`;
        document.getElementById('mentor-count').textContent = `(${mentorList.querySelectorAll('input[name="mentor_id"]:checked').length})`;
        nextBtn.disabled = !(batchList.querySelectorAll('input:checked').length > 0 && mentorList.querySelectorAll('input[name="mentor_id"]:checked').length === 1);
    }

    batchList.addEventListener('change', updateCounts);
    mentorList.addEventListener('change', updateCounts);

    nextBtn.addEventListener('click', () => {
        selectedBatches = Array.from(batchList.querySelectorAll('input:checked')).map(cb => ({ id: cb.value, name: cb.nextElementSibling.textContent }));
        selectedMentor = mentorList.querySelector('input[name="mentor_id"]:checked').value;
        currentBatchIndex = 0;
        scheduledData = [];
        showScheduleModal();
    });

    function showScheduleModal() {
        if (currentBatchIndex < selectedBatches.length) {
            const batch = selectedBatches[currentBatchIndex];
            document.getElementById('schedule-modal-title').textContent = `Schedule for ${batch.name}`;
            document.getElementById('schedule-batch-id').value = batch.id;
            scheduleModal.style.display = 'flex';
            document.getElementById('modal-next-btn').textContent = (currentBatchIndex < selectedBatches.length - 1) ? 'Next Batch' : 'Finish';
        } else {
            scheduleModal.style.display = 'none';
            showReviewPage();
        }
    }

    scheduleForm.addEventListener('submit', function(e) {
        e.preventDefault();
        scheduledData.push({
            batch_id: document.getElementById('schedule-batch-id').value,
            start_date: document.getElementById('start-date').value,
            day_of_week: document.getElementById('day-of-week').value,
            time: document.getElementById('time').value,
            num_weeks: document.getElementById('num-weeks').value,
            batch_name: selectedBatches[currentBatchIndex].name // For review page display
        });
        currentBatchIndex++;
        showScheduleModal();
    });

    document.getElementById('modal-next-btn').addEventListener('click', showScheduleModal);

    function showReviewPage() {
        scheduleModal.style.display = 'none';
        document.querySelector('.card').style.display = 'none';
        reviewPage.style.display = 'block';

        const mentorName = mentorList.querySelector('input[name="mentor_id"]:checked').nextElementSibling.textContent;
        document.getElementById('review-mentor-name').textContent = `Mentor: ${mentorName}`;

        const reviewTableBody = document.getElementById('review-table-body');
        reviewTableBody.innerHTML = scheduledData.map(s => `<tr><td>${s.batch_name}</td><td>${s.start_date} - Every ${document.getElementById('day-of-week').options[parseInt(s.day_of_week)].text} at ${s.time} for ${s.num_weeks} weeks</td></tr>`).join('');
    }

    document.getElementById('edit-schedule-btn').addEventListener('click', () => {
        reviewPage.style.display = 'none';
        document.querySelector('.card').style.display = 'block';
        currentBatchIndex = 0;
        scheduledData = [];
        showScheduleModal();
    });

    document.getElementById('assign-btn').addEventListener('click', async () => {
        const payload = {
            mentor_id: selectedMentor,
            schedules: scheduledData
        };
        const response = await fetchData('/api/admin/assign_and_schedule', 'POST', payload);
        showAlert(response.message, response.success ? 'success' : 'danger');
        if (response.success) {
            window.location.reload();
        }
    });

    document.querySelector('#schedule-modal .close-button').addEventListener('click', () => {
        scheduleModal.style.display = 'none';
        // Reset state if modal closed manually
        selectedBatches = [];
        selectedMentor = null;
        currentBatchIndex = 0;
        scheduledData = [];
        document.querySelector('.card').style.display = 'block';
        reviewPage.style.display = 'none';
    });

    loadAssignmentData();
});