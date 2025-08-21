// Global state
let userMenuOpen = false;
let mobileMenuOpen = false;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    handleEventHighlighting();
    initializeProfileCompletionPopup();
});

// Initialize application
function initializeApp() {
    initializeClickOutside();
    initializeKeyboardNavigation();
    initializeAnimations();
    initializeFormValidation();
    initializeTooltips();
    
    // Initialize Feather icons if available
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Handle event highlighting from dashboard links
function handleEventHighlighting() {
    // Check if there's a hash in the URL (e.g., #event-123)
    if (window.location.hash && window.location.hash.startsWith('#event-')) {
        // Extract event ID from hash
        const eventId = window.location.hash.replace('#event-', '');
        highlightEvent(eventId);
    }
}

// Highlight specific event with blue glow
function highlightEvent(eventId) {
    
    // Find the event card by ID or data attribute
    const eventElement = document.querySelector(`[data-event-id="${eventId}"]`) ||
                        document.querySelector(`#event-${eventId}`) ||
                        document.querySelector(`.event-card[data-id="${eventId}"]`);
    
    if (eventElement) {
        // Scroll to the event
        eventElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // Add highlight classes with a slight delay
        setTimeout(() => {
            eventElement.classList.add('event-highlight');
            eventElement.classList.add('event-highlight-pulse');
            
            // Force a style recalculation
            eventElement.offsetHeight;
            
            // Debug: log the computed styles
            const computedStyle = window.getComputedStyle(eventElement);
            
            // Remove the pulse animation after it completes
            setTimeout(() => {
                eventElement.classList.remove('event-highlight-pulse');
            }, 2000);
            
            // Remove all highlighting after 8 seconds (longer for testing)
            setTimeout(() => {
                eventElement.classList.remove('event-highlight');
            }, 8000);
        }, 500); // Small delay to ensure smooth scroll completes first
        
        // Clean up the hash from URL after highlighting
        setTimeout(() => {
            if (history.replaceState) {
                history.replaceState(null, null, window.location.pathname + window.location.search);
            }
        }, 2000); // Increased delay so we can see the effect
    } else {
        console.error('Event element not found for ID:', eventId);
    }
}

// User menu toggle
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    const chevron = document.querySelector('.user-chevron');
    
    if (dropdown) {
        userMenuOpen = !userMenuOpen;
        
        if (userMenuOpen) {
            dropdown.classList.add('show');
            chevron.style.transform = 'rotate(180deg)';
        } else {
            dropdown.classList.remove('show');
            chevron.style.transform = 'rotate(0deg)';
        }
    }
}

// Mobile menu toggle
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    const body = document.body;
    
    if (mobileMenu) {
        mobileMenuOpen = !mobileMenuOpen;
        
        if (mobileMenuOpen) {
            mobileMenu.classList.add('show');
            body.style.overflow = 'hidden';
        } else {
            mobileMenu.classList.remove('show');
            body.style.overflow = '';
        }
    }
}

// Click outside to close menus
function initializeClickOutside() {
    document.addEventListener('click', function(event) {
        // Close user menu if clicking outside
        const userMenu = document.querySelector('.user-menu');
        const userDropdown = document.getElementById('userDropdown');
        
        if (userMenu && userDropdown && !userMenu.contains(event.target)) {
            userDropdown.classList.remove('show');
            const chevron = document.querySelector('.user-chevron');
            if (chevron) {
                chevron.style.transform = 'rotate(0deg)';
            }
            userMenuOpen = false;
        }
        
        // Close mobile menu if clicking outside
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        
        if (mobileMenu && mobileMenuBtn && 
            !mobileMenu.contains(event.target) && 
            !mobileMenuBtn.contains(event.target)) {
            mobileMenu.classList.remove('show');
            document.body.style.overflow = '';
            mobileMenuOpen = false;
        }
    });
}

// Keyboard navigation
function initializeKeyboardNavigation() {
    document.addEventListener('keydown', function(event) {
        // Escape key closes menus
        if (event.key === 'Escape') {
            if (userMenuOpen) {
                toggleUserMenu();
            }
            if (mobileMenuOpen) {
                toggleMobileMenu();
            }
        }
        
        // Enter key activates buttons
        if (event.key === 'Enter' && event.target.classList.contains('user-button')) {
            toggleUserMenu();
        }
    });
}

// Animation utilities
function initializeAnimations() {
    // Add entrance animations to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add hover effects to interactive elements
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(this)) {
                event.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('.form-input');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

// Validate entire form
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('.form-input[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Validate individual field
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let errorMessage = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'Dit veld is verplicht';
    }
    
    // Email validation
    else if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Voer een geldig e-mailadres in';
        }
    }
    
    // Password validation
    else if (type === 'password' && value && value.length < 8) {
        isValid = false;
        errorMessage = 'Wachtwoord moet minimaal 8 karakters lang zijn';
    }
    
    // Phone validation
    else if (field.name === 'telefoonnummer' && value) {
        const phoneRegex = /^[\+]?[0-9\s\-\(\)]{10,}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            errorMessage = 'Voer een geldig telefoonnummer in';
        }
    }
    
    // Display error or success
    if (!isValid) {
        showFieldError(field, errorMessage);
    } else {
        clearFieldError(field);
    }
    
    return isValid;
}

// Show field error
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('error');
    field.style.borderColor = 'var(--error-500)';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// Clear field error
function clearFieldError(field) {
    field.classList.remove('error');
    field.style.borderColor = '';
    
    const existingError = field.parentNode.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Show tooltip
function showTooltip(event) {
    const element = event.target;
    const text = element.getAttribute('data-tooltip');
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.position = 'absolute';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    tooltip.style.zIndex = '1000';
    tooltip.style.background = 'var(--secondary-900)';
    tooltip.style.color = 'white';
    tooltip.style.padding = 'var(--space-2) var(--space-3)';
    tooltip.style.borderRadius = 'var(--radius-md)';
    tooltip.style.fontSize = 'var(--font-size-sm)';
    tooltip.style.boxShadow = 'var(--shadow-lg)';
    tooltip.style.opacity = '0';
    tooltip.style.transition = 'opacity var(--transition-fast)';
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
    
    element._tooltip = tooltip;
}

// Hide tooltip
function hideTooltip(event) {
    const element = event.target;
    if (element._tooltip) {
        element._tooltip.remove();
        delete element._tooltip;
    }
}

// AJAX utilities
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token for non-GET requests
    if (options.method && options.method !== 'GET') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken.value;
        }
    }
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showNotification('Er is een fout opgetreden. Probeer het opnieuw.', 'error');
            throw error;
        });
}
// Loading states
function showLoading(element) {
    element.classList.add('loading');
    element.disabled = true;
}

function hideLoading(element) {
    element.classList.remove('loading');
    element.disabled = false;
}

// Utility functions
function formatDate(date) {
    return new Intl.DateTimeFormat('nl-NL', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

function formatTime(date) {
    return new Intl.DateTimeFormat('nl-NL', {
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Common Events JavaScript Utilities
// Shared functions and utilities for all event templates

// CSRF token helper
function getCSRFToken() {
    // Try to get from meta tag first (most reliable)
    const metaToken = document.querySelector('meta[name=csrf-token]');
    if (metaToken && metaToken.content) {
        return metaToken.content;
    }
    
    // Try to get from input field
    const inputToken = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (inputToken && inputToken.value) {
        return inputToken.value;
    }
    
    // Finally try cookie as fallback
    let cookieValue = getCookie('rap_csrftoken');
    if (cookieValue) {
        return cookieValue;
    }
    
    console.error('CSRF token not found!');
    return null;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Generic toast function that can be used across all event pages
function showNotification(message, type) {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0 mb-1" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1070';
        document.body.appendChild(toastContainer);
    }
    
    // Add toast to container
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    
    // Initialize and show toast (with fallback for missing Bootstrap)
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toast = new bootstrap.Toast(toastContainer.lastElementChild, {
            autohide: true,
            delay: 3000
        });
        toast.show();
        
        // Remove toast element after it's hidden
        toastContainer.lastElementChild.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    } else {
        // Fallback if Bootstrap is not available
        const toastEl = toastContainer.lastElementChild;
        toastEl.style.display = 'block';
        setTimeout(() => {
            toastEl.remove();
        }, 3000);
    }
}


// Export functions for global use
window.toggleUserMenu = toggleUserMenu;
window.toggleMobileMenu = toggleMobileMenu;
window.showNotification = showNotification;
window.makeRequest = makeRequest;
window.highlightEvent = highlightEvent;

// =======================
// PUSH NOTIFICATIONS
// =======================

window.pushNotifications = {
    // Check if push notifications are supported
    isSupported: function() {
        return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    },
    
    // Request notification permission
    requestPermission: async function() {
        if (!this.isSupported()) {
            console.warn('Push notifications not supported');
            return false;
        }
        
        try {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    },
    
    // Get VAPID public key from server
    getVapidKey: async function() {
        try {
            const response = await fetch('/notifications/push/vapid-key/');
            const data = await response.json();
            return data.vapid_public_key;
        } catch (error) {
            console.error('Error getting VAPID key:', error);
            return null;
        }
    },
    
    // Subscribe to push notifications
    subscribe: async function() {
        if (!this.isSupported()) {
            showNotification('Push notificaties worden niet ondersteund in deze browser', 'warning');
            return false;
        }
        
        try {
            // Request permission first
            const hasPermission = await this.requestPermission();
            if (!hasPermission) {
                showNotification('Notificatie toestemming geweigerd', 'warning');
                return false;
            }
            
            // Get service worker registration
            const registration = await navigator.serviceWorker.ready;
            
            // Get VAPID public key
            const vapidKey = await this.getVapidKey();
            if (!vapidKey) {
                showNotification('Kon VAPID sleutel niet ophalen', 'error');
                return false;
            }
            
            // Subscribe to push notifications
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidKey)
            });
            
            // Send subscription to server
            const response = await fetch('/notifications/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });
            
            if (response.ok) {
                showNotification('Push notificaties ingeschakeld!', 'success');
                return true;
            } else {
                const error = await response.json();
                showNotification(`Fout bij inschakelen: ${error.error}`, 'error');
                return false;
            }
            
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            showNotification('Fout bij inschakelen van notificaties', 'error');
            return false;
        }
    },
    
    // Unsubscribe from push notifications
    unsubscribe: async function() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                // Notify server
                await fetch('/notifications/push/subscribe/', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        endpoint: subscription.endpoint
                    })
                });
            }
            
            showNotification('Push notificaties uitgeschakeld', 'info');
            return true;
            
        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
            showNotification('Fout bij uitschakelen van notificaties', 'error');
            return false;
        }
    },
    
    // Check current subscription status
    getSubscriptionStatus: async function() {
        try {
            const response = await fetch('/notifications/push/subscribe/');
            const data = await response.json();
            return data.subscribed;
        } catch (error) {
            console.error('Error checking subscription status:', error);
            return false;
        }
    },
    
    // Send test notification
    sendTest: async function() {
        try {
            const response = await fetch('/notifications/push/test/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (response.ok) {
                showNotification('Test notificatie verzonden!', 'success');
            } else {
                const error = await response.json();
                showNotification(`Fout: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error sending test notification:', error);
            showNotification('Fout bij verzenden test notificatie', 'error');
        }
    },
    
    // Utility function to convert VAPID key
    urlBase64ToUint8Array: function(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
};

// Initialize push notifications on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add push notification button to user menu if supported
    if (window.pushNotifications.isSupported()) {
        window.pushNotifications.getSubscriptionStatus().then(isSubscribed => {
            // Could add a notification settings button here
            console.log('Push notification status:', isSubscribed ? 'subscribed' : 'not subscribed');
        });
    }
});

// =======================
// Profile Completion Popup
// =======================
function initializeProfileCompletionPopup() {
    const popup = document.getElementById('profile-completion-popup');
    if (!popup) return;
    
    // Check if popup was dismissed recently (7 days)
    const dismissedTimestamp = getCookie('profile_completion_dismissed');
    if (dismissedTimestamp) {
        const dismissedDate = new Date(parseInt(dismissedTimestamp));
        const now = new Date();
        const daysDiff = (now - dismissedDate) / (1000 * 60 * 60 * 24);
        
        if (daysDiff < 7) {
            // Still within dismissal period, don't show popup
            return;
        }
    }
    
    // Show popup after a short delay
    setTimeout(() => {
        showProfileCompletionPopup();
    }, 1000);
    
    // Setup event listeners
    setupProfilePopupEventListeners();
}

function showProfileCompletionPopup() {
    const popup = document.getElementById('profile-completion-popup');
    if (!popup || window.location.pathname.startsWith('/users/profile/edit')) return;
    
    // Show popup
    popup.style.display = 'block';
    document.body.classList.add('popup-open');
    
    // Trigger show animation
    setTimeout(() => {
        popup.classList.add('show');
    }, 10);
    
    // Replace feather icons if available
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function hideProfileCompletionPopup() {
    const popup = document.getElementById('profile-completion-popup');
    if (!popup) return;
    
    // Hide popup with animation
    popup.classList.remove('show');
    document.body.classList.remove('popup-open');
    
    // Actually hide after animation
    setTimeout(() => {
        popup.style.display = 'none';
    }, 300);
}

function dismissProfileCompletionPopup() {
    // Set cookie to remember dismissal for 7 days
    const dismissDate = new Date();
    const expiryDate = new Date(dismissDate.getTime() + (2 * 24 * 60 * 60 * 1000)); // 7 days
    
    document.cookie = `profile_completion_dismissed=${dismissDate.getTime()}; expires=${expiryDate.toUTCString()}; path=/; SameSite=Lax`;
    
    hideProfileCompletionPopup();
}

function setupProfilePopupEventListeners() {
    const closeBtn = document.getElementById('profile-popup-close');
    const dismissBtn = document.getElementById('profile-popup-dismiss');
    const overlay = document.getElementById('profile-completion-popup');
    
    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', hideProfileCompletionPopup);
    }
    
    // Dismiss button (sets cookie)
    if (dismissBtn) {
        dismissBtn.addEventListener('click', dismissProfileCompletionPopup);
    }
    
    // Close on overlay click (not popup content)
    if (overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) {
                hideProfileCompletionPopup();
            }
        });
    }
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay && overlay.classList.contains('show')) {
            hideProfileCompletionPopup();
        }
    });
}

// Export profile completion functions
window.showProfileCompletionPopup = showProfileCompletionPopup;
window.hideProfileCompletionPopup = hideProfileCompletionPopup;
