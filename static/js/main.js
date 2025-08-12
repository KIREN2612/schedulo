// Global utilities and shared functionality

// Show alert messages
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.dynamic-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} dynamic-alert`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    
    alert.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-${getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; margin-left: auto; padding: 0.25rem;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => alert.remove(), 300);
        }
    }, 5000);
}

function getAlertIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Form validation utilities
function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Date utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function isOverdue(dateString) {
    const today = new Date();
    const dueDate = new Date(dateString);
    return dueDate < today;
}

// Loading states
function setLoading(element, loading = true) {
    if (loading) {
        element.classList.add('loading');
        const originalText = element.innerHTML;
        element.dataset.originalText = originalText;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    } else {
        element.classList.remove('loading');
        if (element.dataset.originalText) {
            element.innerHTML = element.dataset.originalText;
            delete element.dataset.originalText;
        }
    }
}

// API utilities
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Local storage utilities (for client-side preferences)
function savePreference(key, value) {
    try {
        localStorage.setItem(`taskflow_${key}`, JSON.stringify(value));
    } catch (error) {
        console.warn('Could not save preference:', error);
    }
}

function getPreference(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(`taskflow_${key}`);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.warn('Could not load preference:', error);
        return defaultValue;
    }
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new task (on dashboard)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && window.location.pathname === '/dashboard') {
            e.preventDefault();
            const addTaskBtn = document.getElementById('addTaskBtn');
            if (addTaskBtn) addTaskBtn.click();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="flex"]');
            if (openModal) {
                openModal.style.display = 'none';
            }
        }
    });
    
    // Add ripple effect to buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('.btn, .btn *')) {
            const button = e.target.closest('.btn');
            if (button && !button.classList.contains('btn-icon')) {
                createRipple(e, button);
            }
        }
    });
});

function createRipple(event, element) {
    const circle = document.createElement('span');
    const diameter = Math.max(element.clientWidth, element.clientHeight);
    const radius = diameter / 2;
    
    const rect = element.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - rect.left - radius}px`;
    circle.style.top = `${event.clientY - rect.top - radius}px`;
    circle.classList.add('ripple');
    
    const rippleCSS = `
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: rippleEffect 0.6s linear;
            pointer-events: none;
        }
        @keyframes rippleEffect {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    
    if (!document.querySelector('#ripple-styles')) {
        const style = document.createElement('style');
        style.id = 'ripple-styles';
        style.textContent = rippleCSS;
        document.head.appendChild(style);
    }
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    
    const ripple = element.querySelector('.ripple');
    if (ripple) ripple.remove();
    
    element.appendChild(circle);
}

// Debounce utility for search/filter functions
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

// Theme utilities (for future dark mode)
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-theme');
    savePreference('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = getPreference('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
});

// Performance monitoring
function measurePerformance(name, fn) {
    return async function(...args) {
        const start = performance.now();
        const result = await fn.apply(this, args);
        const end = performance.now();
        console.log(`${name} took ${end - start} milliseconds`);
        return result;
    };
}

// Error reporting (placeholder for production error tracking)
function reportError(error, context = {}) {
    console.error('Application Error:', {
        message: error.message,
        stack: error.stack,
        context,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
    });
    
    // In production, send to error tracking service
    // Example: Sentry.captureException(error, { extra: context });
}

// Progressive enhancement utilities
function supportsFeature(feature) {
    switch (feature) {
        case 'serviceWorker':
            return 'serviceWorker' in navigator;
        case 'webAnimations':
            return typeof Element.prototype.animate === 'function';
        case 'intersectionObserver':
            return 'IntersectionObserver' in window;
        default:
            return false;
    }
}

// Export utilities for use in other modules
window.TaskFlowUtils = {
    showAlert,
    validateEmail,
    validatePassword,
    formatDate,
    isOverdue,
    setLoading,
    apiRequest,
    savePreference,
    getPreference,
    debounce,
    toggleTheme,
    measurePerformance,
    reportError,
    supportsFeature
};