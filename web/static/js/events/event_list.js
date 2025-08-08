// Event List JavaScript
// Handles tab switching, filtering, attendance management, and toast notifications

function showTab(tabName) {
    // Get all tab contents and buttons
    const allContents = document.querySelectorAll('.tab-content');
    const allButtons = document.querySelectorAll('.nav-link');
    
    // Hide all content
    allContents.forEach(content => {
        content.classList.add('d-none');
    });
    
    // Remove active class from all buttons
    allButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    const targetContent = document.getElementById(tabName + '-content');
    targetContent.classList.remove('d-none');
    
    // Activate the selected button
    const activeButton = document.getElementById(tabName + '-tab');
    activeButton.classList.add('active');
    
    // Store the active tab in sessionStorage for persistence
    sessionStorage.setItem('activeEventTab', tabName);
}

// Clear all filters
function clearFilters() {
    const form = document.getElementById('filter-form');
    form.querySelectorAll('input, select').forEach(input => {
        if (input.type === 'text') {
            input.value = '';
        } else if (input.tagName === 'SELECT') {
            input.selectedIndex = 0;
        }
    });
    form.submit();
}

// Toggle attendance function
async function setAttendance(eventId, present) {
    const presentBtn = document.getElementById(`present-btn-${eventId}`);
    const absentBtn = document.getElementById(`absent-btn-${eventId}`);
    const attendanceCount = document.getElementById(`attendance-count-${eventId}`);
    const userStatusElement = document.querySelector(`[data-event-id="${eventId}"] .user-status`);
    
    // Prevent multiple simultaneous requests
    if (presentBtn.disabled || absentBtn.disabled) {
        return;
    }
    
    // Get CSRF token
    const csrfToken = getCSRFToken();
    if (!csrfToken) {
        console.error('No CSRF token found');
        console.error('Meta tag:', document.querySelector('meta[name=csrf-token]'));
        console.error('Input field:', document.querySelector('input[name=csrfmiddlewaretoken]'));
        console.error('Cookie:', getCookie('rap_csrftoken'));
        showNotification('Beveiligingstoken niet gevonden. Ververs de pagina en probeer opnieuw.', 'error');
        return;
    }
    
    // Disable buttons during request
    presentBtn.disabled = true;
    absentBtn.disabled = true;
    
    try {
        const response = await fetch(`/attendance/set/${eventId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ present: present })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Update button colors
            updateAttendanceButtons(eventId, data.present);
            
            // Update attendance count
            if (attendanceCount) {
                updateAttendanceCount(attendanceCount, data.attendance_count);
            }
            
            // Update user status display
            if (userStatusElement) {
                updateUserStatusDisplay(userStatusElement, data.present);
            }
            
            // Show success message
            showNotification(data.message, 'success');
            
        } else {
            console.error('Failed to update attendance');
            showNotification('Er is een fout opgetreden bij het bijwerken van je aanwezigheid.', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Er is een fout opgetreden bij het bijwerken van je aanwezigheid.', 'error');
    } finally {
        // Always re-enable buttons
        presentBtn.disabled = false;
        absentBtn.disabled = false;
    }
}

// Update attendance buttons with Bootstrap classes
function updateAttendanceButtons(eventId, present) {
    const presentBtn = document.getElementById(`present-btn-${eventId}`);
    const absentBtn = document.getElementById(`absent-btn-${eventId}`);
    
    if (!presentBtn || !absentBtn) return;
    
    // Reset both buttons to default state
    presentBtn.className = 'btn attendance-btn btn-ghost';
    absentBtn.className = 'btn attendance-btn btn-ghost';
    
    // Set active button color
    if (present === true) {
        presentBtn.className = 'btn attendance-btn btn-success';
} else if (present === false) {
        absentBtn.className = 'btn attendance-btn btn-danger';
    }
}

// Update attendance count
function updateAttendanceCount(countElement, newCount) {
    if (!countElement) return;
    countElement.textContent = newCount;
}

// Update user status display
function updateUserStatusDisplay(element, status) {
    if (!element) return;
    
    if (status === true) {
        element.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="rounded-circle bg-success me-2" style="width: 8px; height: 8px;"></div>
                <span class="text-success fw-medium">Je bent aanwezig</span>
            </div>
        `;
    } else if (status === false) {
        element.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="rounded-circle bg-danger me-2" style="width: 8px; height: 8px;"></div>
                <span class="text-error fw-medium">Je bent afwezig</span>
            </div>
        `;
    } else {
        element.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="rounded-circle bg-warning me-2" style="width: 8px; height: 8px;"></div>
                <span class="text-warning fw-medium">Geen reactie</span>
            </div>
        `;
    }
}

// Auto-submit form on filter change and initialize page
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    
    if (filterForm) {
        const filterInputs = filterForm.querySelectorAll('select');
        
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                filterForm.submit();
            });
        });
        
        // Auto-submit search after typing delay
        const searchInput = filterForm.querySelector('input[name="search"]');
        let searchTimeout;
        
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    filterForm.submit();
                }, 500); // Wait 500ms after user stops typing
            });
        }
    }

    // Add event listeners for tab buttons
    const tabButtons = document.querySelectorAll('[data-tab]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            showTab(tabName);
        });
    });

    // Add event listeners for clear filter buttons
    const clearFilterButtons = document.querySelectorAll('.clear-filters-btn');
    clearFilterButtons.forEach(button => {
        button.addEventListener('click', clearFilters);
    });

    // Add event listeners for attendance buttons
    const attendanceButtons = document.querySelectorAll('.attendance-present-btn, .attendance-absent-btn');
    attendanceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventId = this.dataset.eventId;
            const present = this.dataset.attendance === 'true';
            setAttendance(eventId, present);
        });
    });
});
