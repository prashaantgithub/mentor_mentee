document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-link');
    const identifierLabel = document.getElementById('identifier_label');
    const identifierInput = document.getElementById('identifier');
    const roleInput = document.getElementById('role');
    const togglePassword = document.getElementById('togglePassword');
    const password = document.getElementById('password');

    function updateFormForRole(selectedRole) {
        roleInput.value = selectedRole;

        if (selectedRole === 'mentee') {
            identifierLabel.textContent = 'Registration No.';
            identifierInput.placeholder = 'Enter Registration No.';
            identifierInput.type = 'text';
        } else {
            identifierLabel.textContent = 'Email';
            identifierInput.placeholder = 'Enter Email';
            identifierInput.type = 'email';
        }
    }

    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const selectedRole = tab.dataset.role;
                updateFormForRole(selectedRole);
            });
        });
        updateFormForRole('mentee');
    }

    if (togglePassword) {
        togglePassword.addEventListener('click', function () {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    }
});