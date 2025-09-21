document.addEventListener('DOMContentLoaded', function() {
    const addStudentForm = document.getElementById('add-student-form');
    const uploadStudentForm = document.getElementById('upload-student-form');
    const studentListBody = document.getElementById('student-list-body');
    const uploadReviewArea = document.getElementById('upload-review-area');
    const createBatchesBtn = document.getElementById('create-batches-btn');

    async function loadStudents(classId) {
        const response = await fetchData(`/api/admin/class/${classId}/students`);
        if (response.success) {
            studentListBody.innerHTML = '';
            if (response.students.length > 0) {
                response.students.forEach(student => {
                    studentListBody.innerHTML += `<tr><td>${student.reg_no}</td><td>${student.name}</td><td>${student.batch_name}</td></tr>`;
                });
            } else {
                studentListBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No students in this class.</td></tr>';
            }
        }
    }

    if (addStudentForm) {
        addStudentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const classId = window.location.pathname.split('/')[3];
            const formData = new FormData(addStudentForm);
            const response = await fetch(`/api/admin/class/${classId}/add_student`, { method: 'POST', body: formData });
            const data = await response.json();
            showAlert(data.message, data.success ? 'success' : 'danger');
            if (data.success) {
                addStudentForm.reset();
                loadStudents(classId);
            }
        });
    }

    if (uploadStudentForm) {
        uploadStudentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const classId = window.location.pathname.split('/')[3];
            const formData = new FormData(uploadStudentForm);
            const response = await fetch(`/api/admin/class/${classId}/upload_students`, { method: 'POST', body: formData });
            const data = await response.json();
            
            uploadReviewArea.style.display = 'block';
            uploadReviewArea.innerHTML = '';
            
            if (data.success) {
                if (data.to_add.length > 0) {
                    uploadReviewArea.innerHTML += `<h3>Students to Add (${data.to_add.length})</h3><button id="confirm-upload-btn" class="btn btn-primary">Confirm Add All</button><ul id="students-to-add-list"></ul>`;
                    const list = document.getElementById('students-to-add-list');
                    data.to_add.forEach(s => list.innerHTML += `<li>${s.Reg_num} - ${s.Name}</li>`);
                    
                    document.getElementById('confirm-upload-btn').addEventListener('click', async () => {
                        const confirmResponse = await fetchData(`/api/admin/class/${classId}/confirm_upload`, 'POST', { students: data.to_add });
                        showAlert(confirmResponse.message, confirmResponse.success ? 'success' : 'danger');
                        if (confirmResponse.success) {
                            uploadReviewArea.style.display = 'none';
                            uploadStudentForm.reset();
                            loadStudents(classId);
                        }
                    });
                } else { uploadReviewArea.innerHTML += '<p>No new students to add from the file.</p>'; }
                if (data.duplicates && data.duplicates.length > 0) {
                    uploadReviewArea.innerHTML += `<h3>Duplicate Students (${data.duplicates.length})</h3><ul>${data.duplicates.map(d => `<li>${d}</li>`).join('')}</ul>`;
                }
            } else { showAlert(data.message, 'danger'); }
        });
    }

    if (createBatchesBtn) {
        createBatchesBtn.addEventListener('click', async function() {
            const classId = window.location.pathname.split('/')[3];
            const response = await fetchData(`/api/admin/class/${classId}/create_batches`, 'POST');
            showAlert(response.message, response.success ? 'success' : 'danger');
            if (response.success) { loadStudents(classId); }
        });
    }

    if (studentListBody) {
        const classId = window.location.pathname.split('/')[3];
        loadStudents(classId);
    }
});