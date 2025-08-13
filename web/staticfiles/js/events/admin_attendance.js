// Admin Attendance JavaScript
// Handles bulk actions for marking attendance for all players

function bulkAction(action) {
    if (action === 'clear_all' && !confirm('Weet je zeker dat je alle aanwezigheidsgegevens wilt wissen?')) {
        return;
    }
    
    if ((action === 'mark_all_present' || action === 'mark_all_absent') && 
        !confirm(`Weet je zeker dat je alle spelers wilt markeren als ${action === 'mark_all_present' ? 'aanwezig' : 'afwezig'}?`)) {
        return;
    }
    
    // Show loading state
    const buttons = document.querySelectorAll('.bulk-action-btn');
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.innerHTML = '<i data-feather="loader" class="animate-spin"></i> Bezig...';
    });
    
    // Get the event ID from the URL - this needs to be passed as a data attribute or global variable
    const eventId = window.eventId || document.querySelector('[data-event-id]')?.dataset.eventId;
    
    fetch(`/events/admin/bulk-attendance/${eventId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Reload page to update UI
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.error || 'Er is een fout opgetreden', 'error');
            // Reset buttons
            resetBulkButtons();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Er is een fout opgetreden', 'error');
        resetBulkButtons();
    });
}

function resetBulkButtons() {
    const markPresentBtn = document.querySelector('[data-action="mark_all_present"]');
    const markAbsentBtn = document.querySelector('[data-action="mark_all_absent"]');
    const clearAllBtn = document.querySelector('[data-action="clear_all"]');
    
    if (markPresentBtn) {
        markPresentBtn.innerHTML = '<i data-feather="check-circle"></i> Markeer Iedereen Aanwezig';
    }
    if (markAbsentBtn) {
        markAbsentBtn.innerHTML = '<i data-feather="x-circle"></i> Markeer Iedereen Afwezig';
    }
    if (clearAllBtn) {
        clearAllBtn.innerHTML = '<i data-feather="refresh-cw"></i> Wis Alle Aanwezigheid';
    }
    
    const buttons = document.querySelectorAll('.bulk-action-btn');
    buttons.forEach(btn => {
        btn.disabled = false;
    });
    
    // Re-initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    bulkActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            bulkAction(action);
        });
    });
});
