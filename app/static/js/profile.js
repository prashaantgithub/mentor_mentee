document.addEventListener('DOMContentLoaded', () => {
    const passwordForm = document.getElementById('password-change-form');
    const feedbackDiv = document.getElementById('password-feedback');
    const toggleIcons = document.querySelectorAll('.password-toggle-icon');
    const newPasswordField = document.getElementById('new_password');
    const confirmPasswordField = document.getElementById('confirm_password');

    function validatePasswords() {
        const newPassword = newPasswordField.value;
        const confirmPassword = confirmPasswordField.value;

        if (confirmPassword.length > 0 && newPassword !== confirmPassword) {
            feedbackDiv.textContent = 'New passwords do not match.';
            feedbackDiv.classList.add('danger');
            feedbackDiv.classList.remove('success');
            feedbackDiv.style.display = 'block';
        } else {
            feedbackDiv.style.display = 'none';
        }
    }

    if (passwordForm) {
        newPasswordField.addEventListener('input', validatePasswords);
        confirmPasswordField.addEventListener('input', validatePasswords);

        passwordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            feedbackDiv.style.display = 'none';
            feedbackDiv.textContent = '';
            feedbackDiv.classList.remove('success', 'danger');

            const currentPassword = document.getElementById('current_password').value;
            const newPassword = newPasswordField.value;
            const confirmPassword = confirmPasswordField.value;
            
            if (currentPassword === newPassword) {
                feedbackDiv.textContent = 'New password cannot be the same as the current password.';
                feedbackDiv.classList.add('danger');
                feedbackDiv.style.display = 'block';
                return;
            }

            if (newPassword !== confirmPassword) {
                feedbackDiv.textContent = 'New passwords do not match.';
                feedbackDiv.classList.add('danger');
                feedbackDiv.style.display = 'block';
                return;
            }
            
            try {
                const response = await fetch('/api/change_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword,
                        confirm_password: confirmPassword
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    feedbackDiv.textContent = result.message;
                    feedbackDiv.classList.add('success');
                    passwordForm.reset();
                } else {
                    throw new Error(result.message || 'An unknown error occurred.');
                }
            } catch (error) {
                feedbackDiv.textContent = error.message;
                feedbackDiv.classList.add('danger');
            } finally {
                feedbackDiv.style.display = 'block';
            }
        });
    }

    toggleIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const wrapper = this.closest('.password-wrapper');
            const input = wrapper.querySelector('input');
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    });
});