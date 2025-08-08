// Event Form JavaScript
// Handles form interactions, date picker, and recurring event options

document.addEventListener('DOMContentLoaded', function() {
    // Handle recurrence type selection
    const recurrenceTypeField = document.getElementById(window.recurrenceTypeFieldId);
    const recurrenceEndDateField = document.getElementById('recurrence-end-date-field');
    
    if (recurrenceTypeField && recurrenceEndDateField) {
        function toggleRecurrenceEndDate() {
            const selectedValue = recurrenceTypeField.value;
            if (selectedValue && selectedValue !== 'none') {
                recurrenceEndDateField.style.display = 'block';
                const endDateInput = document.getElementById(window.recurrenceEndDateFieldId);
                if (endDateInput) {
                    endDateInput.required = true;
                }
            } else {
                recurrenceEndDateField.style.display = 'none';
                const endDateInput = document.getElementById(window.recurrenceEndDateFieldId);
                if (endDateInput) {
                    endDateInput.required = false;
                }
            }
        }
        
        // Initial state
        toggleRecurrenceEndDate();
        
        // Listen for changes
        recurrenceTypeField.addEventListener('change', toggleRecurrenceEndDate);
    }
    
    // Initialize the datetime picker for event date field
    const dateField = document.getElementById(window.dateFieldId);
    if (dateField && typeof flatpickr !== 'undefined') {
        flatpickr(dateField, {
            enableTime: true,
            dateFormat: "d/m/Y H:i",
            time_24hr: true,
            locale: "nl",
            allowInput: true,
            minDate: "today",
            defaultDate: dateField.value || null,
            onChange: function(selectedDates, dateStr, instance) {
                // Update the input value
                dateField.value = dateStr;
            },
            onReady: function(selectedDates, dateStr, instance) {
                // Add calendar icon click handler
                const calendarIcon = dateField.parentElement.querySelector('.input-group-text');
                if (calendarIcon) {
                    calendarIcon.addEventListener('click', function() {
                        instance.open();
                    });
                    calendarIcon.style.cursor = 'pointer';
                }
            }
        });
        
        // Add input validation for manual entry
        dateField.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^\d]/g, ''); // Remove non-digits
            let formatted = '';
            
            if (value.length >= 2) {
                formatted += value.substr(0, 2) + '/';
            } else {
                formatted += value;
            }
            
            if (value.length >= 4) {
                formatted += value.substr(2, 2) + '/';
            } else if (value.length >= 2) {
                formatted += value.substr(2);
            }
            
            if (value.length >= 8) {
                formatted += value.substr(4, 4) + ' ';
            } else if (value.length >= 4) {
                formatted += value.substr(4);
            }
            
            if (value.length >= 10) {
                formatted += value.substr(8, 2) + ':';
            } else if (value.length >= 8) {
                formatted += value.substr(8);
            }
            
            if (value.length >= 12) {
                formatted += value.substr(10, 2);
            } else if (value.length >= 10) {
                formatted += value.substr(10);
            }
            
            // Limit to dd/mm/yyyy hh:mm format
            if (formatted.length > 16) {
                formatted = formatted.substring(0, 16);
            }
            
            // Only update if the formatted value is different
            if (formatted !== e.target.value) {
                const cursorPos = e.target.selectionStart;
                e.target.value = formatted;
                
                // Restore cursor position
                let newPos = cursorPos;
                if (formatted.length > e.target.value.length) {
                    newPos++;
                }
                e.target.setSelectionRange(newPos, newPos);
            }
        });
        
        // Add pattern validation
        dateField.setAttribute('pattern', '\\d{2}/\\d{2}/\\d{4} \\d{2}:\\d{2}');
        dateField.setAttribute('title', 'Voer een geldige datum en tijd in (dd/mm/jjjj hh:mm)');
    }
    
    // Auto-resize textarea
    const descriptionField = document.getElementById(window.descriptionFieldId);
    if (descriptionField) {
        descriptionField.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Trigger initial resize
        descriptionField.style.height = 'auto';
        descriptionField.style.height = descriptionField.scrollHeight + 'px';
    }
    
    // Handle recurring event update options
    const updateSingleRadio = document.getElementById('update_single');
    const updateAllRadio = document.getElementById('update_all');
    const recurringOptions = document.getElementById('recurring-update-options');
    
    if (updateSingleRadio && updateAllRadio && recurringOptions) {
        function handleRecurringOptionChange() {
            // Add visual feedback for the selected option
            const singleCheckDiv = updateSingleRadio.closest('.form-check');
            const allCheckDiv = updateAllRadio.closest('.form-check');
            
            if (updateSingleRadio.checked) {
                singleCheckDiv.classList.add('border', 'border-warning', 'rounded', 'p-2', 'bg-light');
                allCheckDiv.classList.remove('border', 'border-primary', 'rounded', 'p-2', 'bg-light');
            } else if (updateAllRadio.checked) {
                allCheckDiv.classList.add('border', 'border-primary', 'rounded', 'p-2', 'bg-light');
                singleCheckDiv.classList.remove('border', 'border-warning', 'rounded', 'p-2', 'bg-light');
            }
        }
        
        // Initial state
        handleRecurringOptionChange();
        
        // Listen for changes
        updateSingleRadio.addEventListener('change', handleRecurringOptionChange);
        updateAllRadio.addEventListener('change', handleRecurringOptionChange);
        
        // Add confirmation before submitting if updating all events
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (updateAllRadio.checked) {
                    const futureEventsCount = window.futureRecurringEventsCount || 0;
                    if (futureEventsCount > 0) {
                        const confirmed = confirm(
                            `Weet u zeker dat u alle ${futureEventsCount} toekomstige evenementen in deze reeks wilt bijwerken? ` +
                            'Deze actie kan niet ongedaan worden gemaakt.'
                        );
                        if (!confirmed) {
                            e.preventDefault();
                            return false;
                        }
                    }
                }
            });
        }
    }
});
