// Event Delete JavaScript
// Handles delete options for recurring events

document.addEventListener('DOMContentLoaded', function() {    
    // Update button text based on selected option
    const deleteButtons = document.querySelectorAll('input[name="delete_series"]');
    const submitButton = document.querySelector('button[type="submit"]');
    
    if (deleteButtons.length > 0 && submitButton) {
        deleteButtons.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'true') {
                    submitButton.innerHTML = '<i data-feather="trash-2"></i> Reeks verwijderen';
                } else {
                    submitButton.innerHTML = '<i data-feather="trash-2"></i> Evenement verwijderen';
                }
                // Re-initialize feather icons if available
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            });
        });
    }
});
