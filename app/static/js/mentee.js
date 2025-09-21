document.addEventListener('DOMContentLoaded', () => {
    const passwordChangeModal = document.getElementById('password-change-modal');
    if (passwordChangeModal) {
        const passwordForm = document.getElementById('password-change-form');
        const newPasswordField = document.getElementById('new_password');
        const confirmPasswordField = document.getElementById('confirm_password');
        const errorDiv = document.getElementById('password-error');
        const toggleIcons = document.querySelectorAll('.password-toggle-icon');

        function validatePasswords() {
            const newPassword = newPasswordField.value;
            const confirmPassword = confirmPasswordField.value;
            
            if (newPassword.length > 0 && confirmPassword.length > 0) {
                if (newPassword !== confirmPassword) {
                    errorDiv.textContent = 'Passwords do not match.';
                    errorDiv.style.display = 'block';
                } else {
                    errorDiv.style.display = 'none';
                }
            } else {
                errorDiv.style.display = 'none';
            }
        }

        newPasswordField.addEventListener('input', validatePasswords);
        confirmPasswordField.addEventListener('input', validatePasswords);

        passwordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorDiv.style.display = 'none';
            const newPassword = newPasswordField.value;
            const confirmPassword = confirmPasswordField.value;

            if (newPassword.length < 6) {
                errorDiv.textContent = 'Password must be at least 6 characters long.';
                errorDiv.style.display = 'block';
                return;
            }

            if (newPassword !== confirmPassword) {
                errorDiv.textContent = 'Passwords do not match.';
                errorDiv.style.display = 'block';
                return;
            }

            try {
                const response = await fetch('/set_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ new_password: newPassword, confirm_password: confirmPassword })
                });
                const result = await response.json();
                if (response.ok && result.success) {
                    alert('Password set successfully! The page will now reload.');
                    window.location.reload();
                } else {
                    throw new Error(result.message || 'An unknown error occurred.');
                }
            } catch (error) {
                errorDiv.textContent = error.message;
                errorDiv.style.display = 'block';
            }
        });

        toggleIcons.forEach(icon => {
            icon.addEventListener('click', function() {
                const input = this.closest('.password-wrapper').querySelector('input');
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.classList.toggle('fa-eye');
                this.classList.toggle('fa-eye-slash');
            });
        });
    }

    const profileUpdateModal = document.getElementById('profile-update-modal');
    if (profileUpdateModal) {
        const residenceSelector = document.getElementById('residence-type-selector');
        const detailsContainer = document.getElementById('residence-details-container');

        const residenceTemplates = {
            Hostel: `<div class="form-grid-2">
                        <div class="form-group"><label>Campus Location</label><select name="hostel_location" class="form-control"><option value="Inside">Inside Campus</option><option value="Outside">Outside Campus</option></select></div>
                        <div class="form-group"><label>Hostel Name</label><input type="text" name="hostel_name" class="form-control"></div>
                     </div>`,
            Relatives: `<div class="form-group"><label>Guardian Name</label><input type="text" name="guardian_name" class="form-control"></div>
                        <div class="form-group"><label>Relationship</label><input type="text" name="guardian_relationship" class="form-control"></div>
                        <div class="form-group"><label>Address</label><textarea name="residence_address" class="form-control"></textarea></div>`,
            'PG/Rented': `<div class="form-grid-2">
                            <div class="form-group"><label>Owner Name</label><input type="text" name="pg_owner_name" class="form-control"></div>
                            <div class="form-group"><label>Owner Mobile</label><input type="text" name="pg_owner_mobile" class="form-control"></div>
                          </div>
                          <div class="form-group"><label>Address</label><textarea name="residence_address" class="form-control"></textarea></div>`,
            Parents: `<div class="form-group"><label>Address</label><textarea name="residence_address" class="form-control"></textarea></div>`
        };

        function renderResidenceFields(type) {
            detailsContainer.innerHTML = residenceTemplates[type] || residenceTemplates['Parents'];
        }
        
        residenceSelector.addEventListener('change', (e) => {
            if (e.target.type === 'radio') {
                renderResidenceFields(e.target.value);
            }
        });

        renderResidenceFields('Parents');
    }

    const leaveRequestModal = document.getElementById('leave-request-modal');
    if (leaveRequestModal) {
        const leaveRequestForm = document.getElementById('leave-request-form');
        const cancelLeaveBtn = document.getElementById('cancel-leave-btn');
        const leaveModalInfo = document.getElementById('leave-modal-info');
        const leaveReasonTextarea = document.getElementById('leave-reason');
        const requestButtons = document.querySelectorAll('.request-leave-btn');
        let currentSessionId = null;

        const openLeaveModal = (sessionId, sessionInfo) => {
            currentSessionId = sessionId;
            leaveModalInfo.textContent = `You are requesting leave for the session on ${sessionInfo}. Please provide a reason.`;
            leaveRequestModal.style.display = 'flex';
        };

        const closeLeaveModal = () => {
            leaveRequestModal.style.display = 'none';
            leaveReasonTextarea.value = '';
            currentSessionId = null;
        };

        requestButtons.forEach(button => {
            button.addEventListener('click', () => {
                openLeaveModal(button.dataset.sessionId, button.dataset.sessionInfo);
            });
        });

        cancelLeaveBtn.addEventListener('click', closeLeaveModal);

        leaveRequestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const reason = leaveReasonTextarea.value.trim();
            if (!reason) {
                alert('A reason for the leave is required.');
                return;
            }

            const button = e.target.querySelector('button[type="submit"]');
            button.disabled = true;
            button.textContent = 'Submitting...';

            try {
                const response = await fetch(`/api/mentee/session/${currentSessionId}/request_leave`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reason: reason })
                });
                const result = await response.json();
                alert(result.message);
                
                if (response.ok && result.success) {
                    const requestButton = document.querySelector(`.request-leave-btn[data-session-id='${currentSessionId}']`);
                    if (requestButton) {
                        requestButton.textContent = 'Request Sent';
                        requestButton.disabled = true;
                    }
                    closeLeaveModal();
                }
            } catch (error) {
                alert('An error occurred. Please try again.');
            } finally {
                button.disabled = false;
                button.textContent = 'Submit Request';
            }
        });
    }
});