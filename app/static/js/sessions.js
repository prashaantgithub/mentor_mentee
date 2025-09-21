document.addEventListener('DOMContentLoaded', () => {
    const classFilter = document.getElementById('class-filter');
    const batchFilter = document.getElementById('batch-filter');
    const dayFilter = document.getElementById('day-filter');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    const upcomingSessionsGrid = document.getElementById('upcoming-sessions-grid');
    const noResultsMessage = document.getElementById('no-upcoming-sessions-found');

    if (!upcomingSessionsGrid) return;

    const allUpcomingCards = upcomingSessionsGrid.querySelectorAll('.session-info-card');

    function applyFilters() {
        const selectedClass = classFilter.value;
        const selectedBatch = batchFilter.value;
        const selectedDay = dayFilter.value;
        let visibleCount = 0;

        allUpcomingCards.forEach(card => {
            const cardClass = card.dataset.className;
            const cardBatch = card.dataset.batchName;
            const cardDay = card.dataset.day;

            const classMatch = (selectedClass === 'all') || (selectedClass === cardClass);
            const batchMatch = (selectedBatch === 'all') || (selectedBatch === cardBatch);
            const dayMatch = (selectedDay === 'all') || (selectedDay === cardDay);

            if (classMatch && batchMatch && dayMatch) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        noResultsMessage.style.display = visibleCount === 0 ? 'block' : 'none';
    }

    function resetFilters() {
        classFilter.value = 'all';
        batchFilter.value = 'all';
        dayFilter.value = 'all';
        applyFilters();
    }

    classFilter.addEventListener('change', applyFilters);
    batchFilter.addEventListener('change', applyFilters);
    dayFilter.addEventListener('change', applyFilters);
    clearFiltersBtn.addEventListener('click', resetFilters);
});