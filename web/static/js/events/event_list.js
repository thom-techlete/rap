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
    
    // Initialize view mode functionality
    initializeViewModes();
    
    // Initialize calendar if calendar view is selected
    if (localStorage.getItem('eventViewMode') === 'calendar') {
        switchViewMode('calendar');
        initializeCalendar();
    }
});

// View Mode Management
function initializeViewModes() {
    const viewModeButtons = document.querySelectorAll('.view-mode-btn');
    const savedViewMode = localStorage.getItem('eventViewMode') || 'list';
    console.log('Saved view mode:', savedViewMode);
    // Set initial view mode
    switchViewMode(savedViewMode);
    
    // Add event listeners to view mode buttons
    viewModeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewMode = this.dataset.view;
            switchViewMode(viewMode);
            localStorage.setItem('eventViewMode', viewMode);
            
            // Initialize calendar if switching to calendar view
            if (viewMode === 'calendar') {
                initializeCalendar();
            }
        });
    });
}

function switchViewMode(mode) {
    // Update button states
    const viewModeButtons = document.querySelectorAll('.view-mode-btn');
    viewModeButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.view === mode) {
            btn.classList.add('active');
        }
    });
    
    // Show/hide view content
    const viewContents = document.querySelectorAll('.view-content');
    viewContents.forEach(content => {
        content.classList.add('d-none');
    });
    
    const targetView = document.getElementById(`${mode}-view`);
    if (targetView) {
        targetView.classList.remove('d-none');
    }
}

// Calendar Management
let currentCalendarDate = new Date();
let eventsData = [];

function initializeCalendar() {
    // Load events data from the page
    loadEventsData();
    
    // Populate year selector
    populateYearSelector();
    
    // Set initial month/year
    updateCalendarControls();
    
    // Render calendar
    renderCalendar();
    
    // Add event listeners
    document.getElementById('prev-month').addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
        updateCalendarControls();
        renderCalendar();
    });
    
    document.getElementById('next-month').addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
        updateCalendarControls();
        renderCalendar();
    });
    
    document.getElementById('month-select').addEventListener('change', (e) => {
        currentCalendarDate.setMonth(parseInt(e.target.value));
        updateCalendarControls();
        renderCalendar();
    });
    
    document.getElementById('year-select').addEventListener('change', (e) => {
        currentCalendarDate.setFullYear(parseInt(e.target.value));
        updateCalendarControls();
        renderCalendar();
    });
    
    document.getElementById('today-btn').addEventListener('click', () => {
        currentCalendarDate = new Date();
        updateCalendarControls();
        renderCalendar();
    });
}

function loadEventsData() {
    // Extract events from the page data
    eventsData = [];
    
    // Get events from both upcoming and past events
    const upcomingEvents = document.querySelectorAll('#upcoming-content .timeline-content');
    const pastEvents = document.querySelectorAll('#past-content .timeline-content');
    
    // Process upcoming events
    upcomingEvents.forEach(card => {
        const event = extractEventFromCard(card, true);
        if (event) eventsData.push(event);
    });
    
    // Process past events
    pastEvents.forEach(card => {
        const event = extractEventFromCard(card, false);
        if (event) eventsData.push(event);
    });
}

function extractEventFromCard(card, isUpcoming) {
    try {
        const titleElement = card.querySelector('h3, h5, .card-title');
        const timeElements = card.querySelectorAll('span, div');
        const locationElement = card.querySelector('[data-feather="map-pin"]')?.parentElement?.querySelector('span');
        
        let eventDate = null;
        let eventTitle = '';
        let eventLocation = '';
        let eventType = 'overig';
        
        if (titleElement) {
            eventTitle = titleElement.textContent.trim();
        }
        
        if (locationElement) {
            eventLocation = locationElement.textContent.trim();
        }
        
        // Try to extract date from various possible formats
        timeElements.forEach(element => {
            const text = element.textContent.trim();
            // Look for date patterns like "zaterdag 16 augustus 2025, 18:02"
            const datePattern = /(\w+day|\w+dag)\s+(\d{1,2})\s+(\w+)\s+(\d{4}),?\s+(\d{1,2}):(\d{2})/i;
            const match = text.match(datePattern);
            if (match && !eventDate) {
                const [, , day, monthName, year, hour, minute] = match;
                const monthMap = {
                    'januari': 0, 'februari': 1, 'maart': 2, 'april': 3, 'mei': 4, 'juni': 5,
                    'juli': 6, 'augustus': 7, 'september': 8, 'oktober': 9, 'november': 10, 'december': 11
                };
                const month = monthMap[monthName.toLowerCase()];
                if (month !== undefined) {
                    eventDate = new Date(parseInt(year), month, parseInt(day), parseInt(hour), parseInt(minute));
                }
            }
        });
        
        // Determine event type from badge or other indicators
        const typeElement = card.querySelector('.badge, .event-type-badge');
        if (typeElement) {
            const typeText = typeElement.textContent.toLowerCase();
            if (typeText.includes('training')) eventType = 'training';
            else if (typeText.includes('wedstrijd')) eventType = 'wedstrijd';
            else if (typeText.includes('uitje')) eventType = 'uitje';
            else if (typeText.includes('vergadering')) eventType = 'vergadering';
        }
        
        if (eventTitle && eventDate) {
            return {
                id: `event-${eventTitle.replace(/\s+/g, '-').toLowerCase()}`,
                title: eventTitle,
                date: eventDate,
                location: eventLocation,
                type: eventType,
                isUpcoming: isUpcoming,
                url: card.closest('[onclick]')?.getAttribute('onclick')?.match(/window\.location\.href='([^']+)'/)?.[1]
            };
        }
    } catch (error) {
        console.warn('Error extracting event data:', error);
    }
    
    return null;
}

function populateYearSelector() {
    const yearSelect = document.getElementById('year-select');
    yearSelect.innerHTML = '';
    
    const currentYear = new Date().getFullYear();
    for (let year = currentYear - 2; year <= currentYear + 5; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
}

function updateCalendarControls() {
    const monthNames = [
        'Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
        'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December'
    ];
    
    document.getElementById('calendar-month-year').textContent = 
        `${monthNames[currentCalendarDate.getMonth()]} ${currentCalendarDate.getFullYear()}`;
    
    document.getElementById('month-select').value = currentCalendarDate.getMonth();
    document.getElementById('year-select').value = currentCalendarDate.getFullYear();
}

function renderCalendar() {
    const calendarGrid = document.getElementById('calendar-grid');
    calendarGrid.innerHTML = '';
    
    // Create calendar table
    const table = document.createElement('table');
    table.className = 'table table-borderless mb-0';
    table.style.tableLayout = 'fixed';
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const dayNames = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
    
    dayNames.forEach(day => {
        const th = document.createElement('th');
        th.textContent = day;
        th.className = 'text-center py-3';
        th.style.color = '#6b7280';
        th.style.fontWeight = '600';
        th.style.fontSize = '0.875rem';
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create calendar body
    const tbody = document.createElement('tbody');
    
    // Get first day of month and number of days
    const firstDay = new Date(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth(), 1);
    const lastDay = new Date(currentCalendarDate.getFullYear(), currentCalendarDate.getMonth() + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - (firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1));
    
    // Create calendar weeks
    for (let week = 0; week < 6; week++) {
        const row = document.createElement('tr');
        
        for (let day = 0; day < 7; day++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + (week * 7) + day);
            
            const cell = document.createElement('td');
            cell.className = 'p-1';
            cell.style.height = '120px';
            cell.style.verticalAlign = 'top';
            
            const dayDiv = document.createElement('div');
            dayDiv.className = 'calendar-day h-100 p-2';
            dayDiv.style.borderRadius = '0.5rem';
            dayDiv.style.minHeight = '100px';
            
            // Check if this is current month
            if (currentDate.getMonth() !== currentCalendarDate.getMonth()) {
                dayDiv.style.backgroundColor = '#f9fafb';
                dayDiv.style.color = '#9ca3af';
            } else {
                dayDiv.style.backgroundColor = '#fff';
                dayDiv.style.border = '1px solid #e5e7eb';
                
                // Highlight today
                const today = new Date();
                if (currentDate.toDateString() === today.toDateString()) {
                    dayDiv.style.backgroundColor = '#eff6ff';
                    dayDiv.style.border = '2px solid #3b82f6';
                }
            }
            
            // Add day number
            const dayNumber = document.createElement('div');
            dayNumber.className = 'fw-bold mb-1';
            dayNumber.style.fontSize = '0.875rem';
            dayNumber.textContent = currentDate.getDate();
            dayDiv.appendChild(dayNumber);
            
            // Add events for this day
            const dayEvents = getEventsForDate(currentDate);
            dayEvents.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'calendar-event small p-1 mb-1';
                eventDiv.style.backgroundColor = getEventColor(event.type);
                eventDiv.style.color = 'white';
                eventDiv.style.borderRadius = '0.25rem';
                eventDiv.style.fontSize = '0.75rem';
                eventDiv.style.fontWeight = '500';
                eventDiv.style.cursor = 'pointer';
                eventDiv.textContent = event.title;
                eventDiv.title = `${event.title}\n${event.location}`;
                
                eventDiv.addEventListener('click', () => {
                    // Navigate to event detail (if event ID is available)
                    if (event.url) {
                        window.location.href = event.url;
                    }
                });
                
                dayDiv.appendChild(eventDiv);
            });
            
            cell.appendChild(dayDiv);
            row.appendChild(cell);
        }
        
        tbody.appendChild(row);
        
        // Break if we've gone past the current month and this week is complete
        if (week >= 4 && startDate.getDate() + (week * 7) + 6 > lastDay.getDate()) {
            break;
        }
    }
    
    table.appendChild(tbody);
    calendarGrid.appendChild(table);
}

function getEventsForDate(date) {
    return eventsData.filter(event => {
        const eventDate = new Date(event.date);
        return eventDate.toDateString() === date.toDateString();
    });
}

function getEventColor(eventType) {
    const colors = {
        'training': '#059669',
        'wedstrijd': '#dc2626',
        'uitje': '#7c3aed',
        'vergadering': '#ea580c',
        'overig': '#6b7280'
    };
    return colors[eventType] || colors['overig'];
};
