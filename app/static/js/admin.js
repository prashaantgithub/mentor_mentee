document.addEventListener('DOMContentLoaded', () => {
    const createdBatchesList = document.getElementById('created-batches-list');
    
    // Check if we are on the correct page before running the code
    if (!createdBatchesList) {
        return;
    }

    const studentListModal = document.getElementById('student-list-modal');
    const studentListModalTitle = document.getElementById('student-list-modal-title');
    const studentListModalBody = document.getElementById('student-list-modal-body');

    const openModal = (modal) => modal.style.display = 'flex';

    const openStudentModal = async (batchId, batchName) => {
        studentListModalTitle.textContent = `Students in ${batchName}`;
        studentListModalBody.innerHTML = '<p>Loading students...</p>';
        openModal(studentListModal);

        try {
            const response = await fetch(`/api/admin/batch/${batchId}/students`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();

            if (data && data.success) {
                if (data.students.length > 0) {
                    const table = `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Reg. No</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.students.map(s => `<tr><td>${s.name}</td><td>${s.reg_num}</td></tr>`).join('')}
                            </tbody>
                        </table>`;
                    studentListModalBody.innerHTML = table;
                } else {
                    studentListModalBody.innerHTML = '<p>No students found in this batch.</p>';
                }
            } else {
                studentListModalBody.innerHTML = '<p>Could not load students. Please try again.</p>';
            }
        } catch (error) {
            console.error('Fetch error:', error);
            studentListModalBody.innerHTML = '<p>An error occurred while fetching student data.</p>';
        }
    };

    createdBatchesList.addEventListener('click', (e) => {
        const link = e.target.closest('.view-students-link');
        if (link) {
            e.preventDefault();
            const batchId = link.dataset.batchId;
            const batchName = link.dataset.batchName;
            openStudentModal(batchId, batchName);
        }
    });
});