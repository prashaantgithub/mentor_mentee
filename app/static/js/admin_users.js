document.addEventListener('DOMContentLoaded', function() {
    // Get references to all the interactive elements on the page
    const roleFilter = document.getElementById('role-filter');
    const menteeFilters = document.getElementById('mentee-filters');
    const mentorFilters = document.getElementById('mentor-filters');
    const classFilter = document.getElementById('class-filter');
    const batchFilter = document.getElementById('batch-filter');
    const departmentFilter = document.getElementById('department-filter');
    const searchInput = document.getElementById('search-input');
    const sortBy = document.getElementById('sort-by');
    const userList = document.getElementById('user-list');
    const userCount = document.getElementById('user-count');

    let debounceTimer;

    // A helper function to prevent firing the search on every single keystroke
    const debounce = (func, delay) => {
        return function(...args) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    // The main function to fetch and display users based on current filters
    async function fetchAndRenderUsers() {
        userList.innerHTML = '<p class="text-muted">Loading users...</p>';
        userCount.textContent = '';

        // Construct the API query string from all filter values
        const params = new URLSearchParams({
            role: roleFilter.value,
            department: departmentFilter.value,
            class_id: classFilter.value,
            batch_id: batchFilter.value,
            search_term: searchInput.value,
            sort_by: sortBy.value
        });

        try {
            const response = await fetch(`/api/admin/filter_users?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            userList.innerHTML = '';
            userCount.textContent = `Showing ${data.users.length} user(s).`;

            if (data.users.length === 0) {
                userList.innerHTML = '<div class="alert alert-info">No users found matching your criteria.</div>';
                return;
            }

            data.users.forEach(user => {
                let userDetails = '';
                let userLink = '#';

                if (roleFilter.value === 'mentee') {
                    userDetails = `
                        <p><strong>Reg. No:</strong> ${user.reg_num || 'N/A'}</p>
                        <p><strong>Class:</strong> ${user.class || 'N/A'}</p>
                        <p><strong>Batch:</strong> ${user.batch || 'N/A'}</p>
                    `;
                    userLink = `/admin/mentee/${user.id}`;
                } else { // Mentor
                     userDetails = `<p><strong>Email:</strong> ${user.email || 'Not Provided'}</p>`;
                     userLink = `/admin/mentor/${user.id}`;
                }
                
                const userCardHTML = `
                    <a href="${userLink}" class="user-card-link" style="text-decoration: none;">
                        <div class="user-card">
                            <h5>${user.name}</h5>
                            ${userDetails}
                        </div>
                    </a>
                `;
                userList.insertAdjacentHTML('beforeend', userCardHTML);
            });

        } catch (error) {
            console.error("Failed to fetch users:", error);
            userList.innerHTML = '<div class="alert alert-danger">An error occurred while fetching users.</div>';
        }
    }

    // Event listener for the main role selector
    roleFilter.addEventListener('change', () => {
        const isMentee = roleFilter.value === 'mentee';
        
        menteeFilters.style.display = isMentee ? 'flex' : 'none';
        mentorFilters.style.display = isMentee ? 'none' : 'flex';
        
        sortBy.querySelector('option[value="reg_num_asc"]').disabled = !isMentee;
        sortBy.querySelector('option[value="reg_num_desc"]').disabled = !isMentee;
        if (!isMentee && sortBy.value.includes('reg_num')) {
            sortBy.value = 'name_asc';
        }
        
        classFilter.value = '';
        batchFilter.value = '';
        departmentFilter.value = '';
        searchInput.value = '';
        fetchAndRenderUsers();
    });

    // Event listener for the class filter to dynamically populate batches
    classFilter.addEventListener('change', async () => {
        const classId = classFilter.value;
        batchFilter.innerHTML = '<option value="">All Batches</option>';
        batchFilter.disabled = true;

        if (classId) {
            try {
                const response = await fetch(`/api/admin/class/${classId}/batches`);
                const data = await response.json();
                if (data.success) {
                    data.batches.forEach(batch => {
                        batchFilter.innerHTML += `<option value="${batch.id}">${batch.name}</option>`;
                    });
                    batchFilter.disabled = false;
                }
            } catch (error) {
                console.error("Failed to fetch batches:", error);
            }
        }
        fetchAndRenderUsers();
    });
    
    batchFilter.addEventListener('change', fetchAndRenderUsers);
    departmentFilter.addEventListener('change', fetchAndRenderUsers);
    sortBy.addEventListener('change', fetchAndRenderUsers);
    
    searchInput.addEventListener('input', debounce(fetchAndRenderUsers, 400));
    
    fetchAndRenderUsers();
});