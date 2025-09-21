document.addEventListener('DOMContentLoaded', () => {
    let selectedMenteeId = null;
    let selectedMenteeName = null;
    const sessionId = window.location.pathname.split('/')[3];
    let menteeDataState = {}; 

    const menteeListItems = document.querySelectorAll('.mentee-list li');
    const initialStateDiv = document.getElementById('panel-initial-state');
    const selectedStateDiv = document.getElementById('panel-selected-state');
    const selectedMenteeNameElem = document.getElementById('selected-mentee-name');
    const recordTypeSelector = document.getElementById('record-type-selector');
    const dynamicFormContainer = document.getElementById('dynamic-form-container');
    const absentCheckbox = document.getElementById('mark-absent-checkbox');
    const endSessionBtn = document.getElementById('end-session-btn');
    const menteeActionsDiv = document.querySelector('.mentee-actions');
    const recordEntrySection = document.getElementById('record-entry-section');
    const leaveApprovedMessageDiv = document.getElementById('leave-approved-message');

    const singleSubjectFormHTML = `
        <div class="subject-entry-form" style="border-top: 1px solid var(--live-border-color); margin-top: 1rem; padding-top: 1rem;">
            <div class="form-group"><label>Subject Code / Name</label><input type="text" name="subject_code_name" class="form-control"></div>
            <div class="form-group"><label>GRADE</label><input type="text" name="grade" class="form-control"></div>
            <div class="form-group"><label>GPA</label><input type="number" step="0.01" name="gpa" class="form-control"></div>
            <div class="form-group"><label>CGPA</label><input type="number" step="0.01" name="cgpa" class="form-control"></div>
            <div class="form-group"><label>ATTENDANCE %</label><input type="number" step="0.01" name="attendance_percentage" class="form-control"></div>
            <div class="form-group"><label>CIA-1</label><input type="number" step="0.01" name="cia_1" class="form-control"></div>
            <div class="form-group"><label>CIA-2</label><input type="number" step="0.01" name="cia_2" class="form-control"></div>
            <div class="form-group"><label>CIA-3</label><input type="number" step="0.01" name="cia_3" class="form-control"></div>
            <div class="form-group"><label>Overall CIA</label><input type="number" step="0.01" name="overall_cia" class="form-control"></div>
            <div class="ese-attempts-container">
                <div class="form-group"><label>ESE ATTEMPT - 1</label><input type="number" step="0.01" name="ese_attempt_1" class="form-control"></div>
            </div>
            <button type="button" class="btn btn-link btn-sm add-ese-attempt-btn">+ Add Another ESE Attempt</button>
            <div class="form-group"><label>Suggestions by Mentor to Improve</label><textarea name="suggestions_by_mentor" class="form-control"></textarea></div>
            <div class="form-group"><label><input type="checkbox" name="course_acceleration_deceleration"> Course Acceleration / De-Acceleration</label></div>
        </div>`;


    const formTemplates = {
        placement_information: `<form data-form-type="placement_information"><h4>Placement Information</h4><div class="form-group"><label>Company Name</label><input type="text" name="company_name" class="form-control" required></div><div class="form-group"><label>Company Location</label><input type="text" name="company_location" class="form-control"></div><div class="form-group"><label>Interview Date</label><input type="date" name="interview_date" class="form-control" required></div><div class="form-group"><label>No. Of Rounds Attended</label><input type="number" name="rounds_attended" class="form-control" required></div><div class="form-group"><label>Internship Provided</label><select name="internship_provided" class="form-control" required><option value="">-- Select --</option><option value="true">Yes</option><option value="false">No</option></select></div><div class="form-group"><label>Annual CTC (Rs.)</label><input type="number" step="0.01" name="annual_ctc" class="form-control"></div><div class="form-group"><label>Stipend Amount (Rs.)</label><input type="number" step="0.01" name="stipend_amount" class="form-control"></div><div class="form-group"><label>Interview Status</label><input type="text" name="interview_status" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        research_record: `<form data-form-type="research_record"><h4>Research Record</h4><div class="form-group"><label>Title</label><input type="text" name="title" class="form-control" required></div><div class="form-group"><label>Conference / Journal / Patent Name</label><input type="text" name="publication_name" class="form-control" required></div><div class="form-group"><label>ISSN/E-ISSN / ISBN Number</label><input type="text" name="identifier_number" class="form-control"></div><div class="form-group"><label>Publication Date</label><input type="date" name="publication_date" class="form-control" required></div><div class="form-group"><label>Type of Publication (Scopus / SCI / UGC, etc)</label><input type="text" name="publication_type" class="form-control" required></div><div class="form-group"><label>Status of Publication</label><input type="text" name="publication_status" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        academic_mark_details: `<div data-form-type="academic_mark_details" class="multi-record-form"><h4>Academic Semester Mark Details</h4><div class="subjects-container"></div><div class="form-actions mt-3"><button type="button" class="btn btn-secondary add-subject-btn">Add Another Subject</button><button type="button" class="btn btn-primary save-multi-subject-btn">Save All Academic Records</button></div></div>`,
        honors_minor_marks: `<div data-form-type="honors_minor_marks" class="multi-record-form"><h4>Honors / Minors Marks Details</h4><div class="form-group"><label for="honors_minor_type">Course Type</label><select id="honors_minor_type" name="course_type" class="form-control" required><option value="">-- Select Type --</option><option value="Honors">Honors</option><option value="Minors">Minors</option></select></div><div class="subjects-container"></div><div class="form-actions mt-3" style="display:none;"><button type="button" class="btn btn-secondary add-subject-btn">Add Another Subject</button><button type="button" class="btn btn-primary save-multi-subject-btn">Save All Records</button></div></div>`,
        mentor_meeting_details: `<form data-form-type="mentor_meeting_details"><h4>Mentor Meeting Details</h4><div class="form-group"><label>Points Discussed</label><textarea name="points_discussed" class="form-control" required></textarea></div><div class="form-group"><label>Remarks Given</label><textarea name="remarks_given" class="form-control" required></textarea></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        awards_achievements: `<form data-form-type="awards_achievements"><h4>Awards and Achievements</h4><div class="form-group"><label>Award / Achievement Name</label><input type="text" name="award_achievement_name" class="form-control" required></div><div class="form-group"><label>Award / Achievement Type</label><input type="text" name="award_achievement_type" class="form-control"></div><div class="form-group"><label>Conducted By</label><input type="text" name="conducted_by" class="form-control" required></div><div class="form-group"><label>Date</label><input type="date" name="date" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        cocurricular_activity: `<form data-form-type="cocurricular_activity"><h4>Co-Curricular Activity Record</h4><div class="form-group"><label>Activity Name</label><input type="text" name="activity_name" class="form-control" required></div><div class="form-group"><label>Activity Type</label><input type="text" name="activity_type" class="form-control"></div><div class="form-group"><label>Conducted By</label><input type="text" name="conducted_by" class="form-control" required></div><div class="form-group"><label>Date</label><input type="date" name="date" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        extracurricular_activity: `<form data-form-type="extracurricular_activity"><h4>Extra-Curricular Activity Record</h4><div class="form-group"><label>Activity Name</label><input type="text" name="activity_name" class="form-control" required></div><div class="form-group"><label>Activity Type</label><input type="text" name="activity_type" class="form-control"></div><div class="form-group"><label>Conducted By</label><input type="text" name="conducted_by" class="form-control" required></div><div class="form-group"><label>Date</label><input type="date" name="date" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`,
        internship_information: `<form data-form-type="internship_information"><h4>Internship Information</h4><div class="form-group"><label>Company Name</label><input type="text" name="company_name" class="form-control" required></div><div class="form-group"><label>Duration From</label><input type="date" name="duration_from" class="form-control" required></div><div class="form-group"><label>Duration To</label><input type="date" name="duration_to" class="form-control" required></div><div class="form-group"><label>Sem</label><input type="text" name="sem" class="form-control" required></div><div class="form-group"><label>Technology / Domain</label><input type="text" name="technology_domain" class="form-control" required></div><div class="form-group"><label>Internship Project Details</label><textarea name="internship_project_details" class="form-control"></textarea></div><div class="form-group"><label>Company Location</label><input type="text" name="company_location" class="form-control"></div><div class="form-group"><label>Internship Status</label><input type="text" name="internship_status" class="form-control" required></div><button type="submit" class="btn btn-primary">Save Record</button></form>`
    };

    function collectFormData(container) {
        const data = {};
        container.querySelectorAll('input, select, textarea').forEach(field => {
            if (field.name) {
                if (field.type === 'checkbox') {
                    data[field.name] = field.checked;
                } else {
                    data[field.name] = field.value;
                }
            }
        });
        return data;
    }

    function validateForm(form, formType) {
        const requiredInputs = form.querySelectorAll('[required]');
        for (const input of requiredInputs) {
            if (!input.value.trim()) {
                alert(`Error: '${input.closest('.form-group').querySelector('label').textContent}' is a required field.`);
                input.focus();
                return false;
            }
        }

        if (formType === 'internship_information') {
            const fromDate = form.elements['duration_from'].value;
            const toDate = form.elements['duration_to'].value;
            if (fromDate && toDate && fromDate > toDate) {
                alert('Error: "Duration From" date cannot be after "Duration To" date.');
                form.elements['duration_to'].focus();
                return false;
            }
        }
        return true;
    }

    function setFormEnabled(container, enabled) {
        container.querySelectorAll('input, select, textarea').forEach(el => {
            el.disabled = !enabled;
        });
        
        const saveButton = container.querySelector('button[type="submit"]');
        if (saveButton) {
            saveButton.style.display = enabled ? 'block' : 'none';
        }
       
        const formWrapper = container.closest('[data-form-type]');
        if (formWrapper) {
            let editBtn = formWrapper.querySelector('.edit-btn');
            
            if (formWrapper.classList.contains('multi-record-form')) {
                const formActions = formWrapper.querySelector('.form-actions');
                if (formActions) formActions.style.display = enabled ? 'flex' : 'none';
                if (editBtn) editBtn.style.display = enabled ? 'none' : 'block';
            } else {
                if (!editBtn) {
                     formWrapper.insertAdjacentHTML('beforeend', `<button type="button" class="btn btn-secondary edit-btn mt-3" style="display: none;">Edit</button>`);
                     editBtn = formWrapper.querySelector('.edit-btn');
                }
                if (editBtn) editBtn.style.display = !enabled ? 'block' : 'none';
            }
        }

        container.querySelectorAll('.ese-attempts-container').forEach(eseContainer => {
            const addBtn = eseContainer.closest('.subject-entry-form').querySelector('.add-ese-attempt-btn');
            if (addBtn) {
                if (eseContainer.children.length >= 4) {
                    addBtn.style.display = 'none';
                } else {
                    addBtn.style.display = enabled ? 'inline-block' : 'none';
                }
            }
        });
    }
    
    function populateFormFields(formElement, data) {
        if (!formElement) return;

        for (const key in data) {
            const field = formElement.elements ? formElement.elements[key] : formElement.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = !!data[key];
                } else if (field.type === 'date' && data[key]) {
                    field.value = new Date(data[key]).toISOString().split('T')[0];
                } else if (field.tagName === 'SELECT') {
                    const dataValueString = String(data[key] || '').toLowerCase(); 
                    const foundOption = Array.from(field.options).find(option => option.value.toLowerCase() === dataValueString);
                    if (foundOption) {
                        field.value = foundOption.value;
                    } else {
                        field.value = String(data[key] || ''); 
                    }
                }
                else {
                    field.value = data[key] || '';
                }
            }
        }
    }

    function resetRecordTypeSelector() {
        recordTypeSelector.value = '';
    }

        async function showForm(formType) {
        dynamicFormContainer.innerHTML = '';
        if (!formType) return;
        dynamicFormContainer.innerHTML = formTemplates[formType] || '';
        const formWrapper = dynamicFormContainer.querySelector('[data-form-type]');
        if (!formWrapper) return;
        
        await fetchMenteeRecordsAndSetInitialState();
        let localData = menteeDataState[selectedMenteeId] ? menteeDataState[selectedMenteeId][formType] : null;

        const isMultiRecord = ['academic_mark_details', 'honors_minor_marks'].includes(formType);

        if (isMultiRecord) {
            const subjectsContainer = formWrapper.querySelector('.subjects-container');
            subjectsContainer.innerHTML = ''; 
            
            let recordsToDisplay = (localData && Array.isArray(localData) && localData.length > 0) ? localData : [];

            if (recordsToDisplay.length > 0) {
                if (formType === 'honors_minor_marks') {
                    const honorsMinorTypeSelector = formWrapper.querySelector('#honors_minor_type');
                    if (honorsMinorTypeSelector && recordsToDisplay[0].semester) {
                        honorsMinorTypeSelector.value = recordsToDisplay[0].semester;
                        honorsMinorTypeSelector.disabled = true;
                    }
                }
                recordsToDisplay.forEach(record => {
                    subjectsContainer.insertAdjacentHTML('beforeend', singleSubjectFormHTML);
                    const newSubjectDiv = subjectsContainer.lastElementChild;
                    
                    for(let i = 1; i <= 4; i++) {
                        if (record[`ese_attempt_${i}`] !== undefined && record[`ese_attempt_${i}`] !== null && i > 1) {
                            const eseContainer = newSubjectDiv.querySelector('.ese-attempts-container');
                            const existingAttempts = eseContainer.children.length;
                            if (existingAttempts < i) { 
                                for (let j = existingAttempts + 1; j <= i; j++) {
                                     eseContainer.insertAdjacentHTML('beforeend', `<div class="form-group"><label>ESE ATTEMPT - ${j}</label><input type="number" step="0.01" name="ese_attempt_${j}" class="form-control"></div>`);
                                }
                            }
                        }
                    }
                    populateFormFields(newSubjectDiv, record);
                    setFormEnabled(newSubjectDiv, false); 
                    newSubjectDiv.querySelector('.add-ese-attempt-btn').style.display = 'none';
                });
                
                if (!formWrapper.querySelector('.edit-btn')) { 
                    formWrapper.insertAdjacentHTML('beforeend', `<button type="button" class="btn btn-secondary edit-btn mt-3">Edit Records</button>`);
                }
                formWrapper.querySelector('.form-actions').style.display = 'none'; 

            } else if (formType === 'academic_mark_details') {
                subjectsContainer.innerHTML = singleSubjectFormHTML.replace('style="border-top: 1px solid var(--live-border-color); margin-top: 1rem; padding-top: 1rem;"', '');
                setFormEnabled(subjectsContainer.firstElementChild, true);
                formWrapper.querySelector('.form-actions').style.display = 'flex';
            } else if (formType === 'honors_minor_marks') {
                formWrapper.querySelector('.form-actions').style.display = 'none';
            }
        } else {
            // Corrected logic for ALL single-record forms, including Mentor Meeting Details
            const form = formWrapper;
            if (localData) {
                populateFormFields(form, localData);
                setFormEnabled(form, false); 
            } else {
                setFormEnabled(form, true); 
            }
        }
    }

    async function fetchMenteeRecordsAndSetInitialState() {
        if (!selectedMenteeId) return;
        menteeDataState[selectedMenteeId] = {}; 
        
        try {
            const response = await fetch(`/api/mentor/session/get_records?session_id=${sessionId}&mentee_id=${selectedMenteeId}`);
            const result = await response.json();
            if (result.success && result.records) {
                for (const formType in result.records) {
                    if (result.records[formType] && result.records[formType].length > 0) {
                        menteeDataState[selectedMenteeId][formType] = ['academic_mark_details', 'honors_minor_marks'].includes(formType) 
                                                                        ? result.records[formType] 
                                                                        : result.records[formType][0];
                    }
                }
            }
        } catch (error) {
            console.error("Failed to fetch records:", error);
            menteeDataState[selectedMenteeId] = {};
        }
    }
    
    async function selectMentee(menteeItem) {
        menteeListItems.forEach(item => item.classList.remove('selected'));
        menteeItem.classList.add('selected');
        selectedMenteeId = menteeItem.dataset.menteeId;
        selectedMenteeName = menteeItem.dataset.menteeName;
        const hasLeave = menteeItem.dataset.hasLeave === 'true';
        
        await fetch('/api/mentor/session/' + sessionId + '/start', { method: 'POST' });

        await fetchMenteeRecordsAndSetInitialState(); 

        selectedMenteeNameElem.textContent = `Recording for: ${selectedMenteeName}`;
        initialStateDiv.style.display = 'none';
        selectedStateDiv.style.display = 'block';
        dynamicFormContainer.innerHTML = '';
        resetRecordTypeSelector();
        
        if (hasLeave) {
            menteeActionsDiv.style.display = 'none';
            recordEntrySection.style.display = 'none';
            leaveApprovedMessageDiv.textContent = `${selectedMenteeName} has an approved leave for this session.`;
            leaveApprovedMessageDiv.style.display = 'block';
            absentCheckbox.checked = true;
            absentCheckbox.disabled = true;
            recordTypeSelector.disabled = true;
        } else {
            menteeActionsDiv.style.display = 'block';
            recordEntrySection.style.display = 'block';
            leaveApprovedMessageDiv.style.display = 'none';
            absentCheckbox.disabled = false;

            const attendanceResponse = await fetch(`/api/mentor/session/get_attendance?session_id=${sessionId}&mentee_id=${selectedMenteeId}`);
            const attendanceData = await attendanceResponse.json();
            absentCheckbox.checked = attendanceData.is_absent;
            recordTypeSelector.disabled = attendanceData.is_absent;
        }
    }

    async function handleAttendanceChange() {
        const isChecked = absentCheckbox.checked;
        recordTypeSelector.disabled = isChecked;
        if (isChecked) {
            dynamicFormContainer.innerHTML = '';
            resetRecordTypeSelector();
        }
        try {
            const response = await fetch('/api/mentor/session/attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    mentee_id: selectedMenteeId,
                    status: isChecked ? 'Absent' : 'Present'
                })
            });
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || "Failed to update attendance.");
            }
        } catch (error) {
            console.error('Failed to update attendance:', error);
            alert('Could not update attendance. Please try again.');
            absentCheckbox.checked = !isChecked; 
            recordTypeSelector.disabled = !absentCheckbox.checked; 
        }
    }
    
    async function handleMultiSubjectFormSubmit(formWrapper) {
        const formType = formWrapper.dataset.formType;
        const records = [];
        let anyFieldFilled = false;
        formWrapper.querySelectorAll('.subject-entry-form').forEach(subjectDiv => {
            const dataObject = collectFormData(subjectDiv);
            if (Object.values(dataObject).some(val => val !== false && typeof val === 'string' && val.trim() !== '' && !['course_acceleration_deceleration'].includes(val))) {
                records.push(dataObject);
                anyFieldFilled = true;
            }
        });

        if (!anyFieldFilled && records.length === 0) {
            alert("Please fill in details for at least one subject.");
            return;
        }

        const payload = {
            mentee_id: selectedMenteeId,
            session_id: sessionId,
            form_type: formType,
            records: records
        };
        
        if (formType === 'honors_minor_marks') {
            const courseTypeSelect = formWrapper.querySelector('[name="course_type"]');
            const courseType = courseTypeSelect.value;
            if (!courseType) {
                alert("Please select a course type (Honors or Minors).");
                return;
            }
            payload.course_type = courseType;
        }

        const button = formWrapper.querySelector('.save-multi-subject-btn');
        if (button) {
            button.disabled = true;
            button.textContent = 'Saving...';
        }

        try {
            const response = await fetch('/api/mentor/session/add_multi_record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                alert('Records saved successfully!');
                menteeDataState[selectedMenteeId][formType] = records.map(record => ({...record}));
                await showForm(formType); 
            } else {
                throw new Error(result.message || 'Failed to save multi-record.');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = 'Save All Academic Records';
                if (formType === 'honors_minor_marks') {
                     button.textContent = 'Save All Records';
                }
            }
        }
    }

    async function handleFormSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formType = form.dataset.formType;

        if (!validateForm(form, formType)) return;
        
        const data = collectFormData(form);
        data.mentee_id = selectedMenteeId;
        data.session_id = sessionId;
        data.form_type = formType;
        
        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.textContent = 'Saving...';
        }
        
        try {
            const response = await fetch('/api/mentor/session/add_record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (result.success) {
                alert('Record saved successfully!');
                menteeDataState[selectedMenteeId][formType] = {...data};
                await showForm(formType); 
            } else {
                throw new Error(result.message || 'Failed to save record.');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = 'Save Record';
            }
        }
    }

    async function handleEndSession() {
        if (!confirm('Are you sure you want to end this session? This action cannot be undone.')) return;
        
        endSessionBtn.disabled = true;
        endSessionBtn.textContent = 'Ending Session...';

        try {
            const response = await fetch('/api/mentor/session/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            const result = await response.json();
            if (result.success) {
                alert('Session ended successfully.');
                window.location.href = '/mentor/completed_sessions';
            } else {
                throw new Error(result.message || 'Failed to end session.');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            endSessionBtn.disabled = false;
            endSessionBtn.textContent = 'End Session';
        }
    }

    dynamicFormContainer.addEventListener('click', e => {
        const formWrapper = e.target.closest('[data-form-type]');
        if (!formWrapper) return; 

        if (e.target.classList.contains('edit-btn')) {
            const isMulti = formWrapper.classList.contains('multi-record-form');
            if (isMulti) {
                formWrapper.querySelectorAll('.subject-entry-form').forEach(subjectDiv => {
                    setFormEnabled(subjectDiv, true);
                    const eseContainer = subjectDiv.querySelector('.ese-attempts-container');
                    const eseAddBtn = subjectDiv.querySelector('.add-ese-attempt-btn');
                    if (eseAddBtn) {
                         eseAddBtn.style.display = (eseContainer.children.length < 4) ? 'inline-block' : 'none';
                    }
                });
                const formActions = formWrapper.querySelector('.form-actions');
                if (formActions) formActions.style.display = 'flex';
                
                const honorsMinorTypeSelector = formWrapper.querySelector('#honors_minor_type');
                if (honorsMinorTypeSelector) honorsMinorTypeSelector.disabled = false;
                
                e.target.remove();
            } else {
                 setFormEnabled(formWrapper, true);
            }
        }
        
        if (e.target.classList.contains('add-subject-btn')) {
            const container = e.target.closest('[data-form-type]').querySelector('.subjects-container');
            container.insertAdjacentHTML('beforeend', singleSubjectFormHTML);
            const newSubjectDiv = container.lastElementChild;
            setFormEnabled(newSubjectDiv, true); 
        }
        
        if (e.target.classList.contains('add-ese-attempt-btn')) {
            const container = e.target.closest('.subject-entry-form').querySelector('.ese-attempts-container');
            const attemptCount = container.children.length + 1;
            if (attemptCount <= 4) {
                const newAttemptHTML = `<div class="form-group"><label>ESE ATTEMPT - ${attemptCount}</label><input type="number" step="0.01" name="ese_attempt_${attemptCount}" class="form-control"></div>`;
                container.insertAdjacentHTML('beforeend', newAttemptHTML);
                if (attemptCount === 4) {
                    e.target.style.display = 'none';
                }
            }
        }
        
        if (e.target.classList.contains('save-multi-subject-btn')) {
            handleMultiSubjectFormSubmit(e.target.closest('[data-form-type]'));
        }
    });

    dynamicFormContainer.addEventListener('change', e => {
        if (e.target.id === 'honors_minor_type') {
            const formWrapper = e.target.closest('[data-form-type]');
            const container = formWrapper.querySelector('.subjects-container');
            const formActions = formWrapper.querySelector('.form-actions');

            if (e.target.value) {
                if(container.children.length === 0){
                    container.innerHTML = singleSubjectFormHTML;
                    setFormEnabled(container.firstElementChild, true);
                }
                formActions.style.display = 'flex';
            } else {
                container.innerHTML = '';
                formActions.style.display = 'none';
            }
        }
    });
    
    menteeListItems.forEach(item => {
        item.addEventListener('click', () => selectMentee(item));
    });

    recordTypeSelector.addEventListener('change', async e => {
        if (!selectedMenteeId) {
            alert('Please select a mentee first.');
            e.target.value = '';
            return;
        }
        await showForm(e.target.value); 
    });
    absentCheckbox.addEventListener('change', handleAttendanceChange);
    dynamicFormContainer.addEventListener('submit', handleFormSubmit);
    endSessionBtn.addEventListener('click', handleEndSession);
});