// Dashboard JavaScript functionality

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return seconds + 's';
    } else if (seconds < 3600) {
        return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's';
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return hours + 'h ' + minutes + 'm';
    }
}

function timeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return diffInSeconds + ' seconds ago';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return minutes + ' minute' + (minutes > 1 ? 's' : '') + ' ago';
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return hours + ' hour' + (hours > 1 ? 's' : '') + ' ago';
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return days + ' day' + (days > 1 ? 's' : '') + ' ago';
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Loading state management
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

// API helper functions
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

// Health check functionality
async function checkSystemHealth() {
    try {
        const health = await apiRequest('/api/health');
        
        const statusElement = document.getElementById('system-health');
        if (statusElement) {
            if (health.status === 'healthy') {
                statusElement.className = 'badge bg-success';
                statusElement.textContent = 'System Healthy';
            } else {
                statusElement.className = 'badge bg-danger';
                statusElement.textContent = 'System Issues';
            }
        }
        
        return health;
    } catch (error) {
        const statusElement = document.getElementById('system-health');
        if (statusElement) {
            statusElement.className = 'badge bg-danger';
            statusElement.textContent = 'Connection Error';
        }
        throw error;
    }
}

// File validation
function validateFile(file) {
    const allowedExtensions = ['.json', '.yaml', '.yml'];
    const maxSizeInMB = 50;
    
    // Check extension
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        return {
            valid: false,
            error: `Invalid file type. Allowed extensions: ${allowedExtensions.join(', ')}`
        };
    }
    
    // Check size
    const sizeInMB = file.size / (1024 * 1024);
    if (sizeInMB > maxSizeInMB) {
        return {
            valid: false,
            error: `File too large. Maximum size: ${maxSizeInMB}MB`
        };
    }
    
    return { valid: true };
}

// Download functionality
function downloadFile(jobId, filename) {
    const url = `/download/${jobId}/${filename}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Export functionality for tables
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get text content and escape quotes
            let text = cols[j].textContent.trim().replace(/"/g, '""');
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

// Initialize tooltips and popovers
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Dark mode toggle
function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }
}

// Search functionality
function createSearchFilter(inputId, targetSelector) {
    const searchInput = document.getElementById(inputId);
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const targets = document.querySelectorAll(targetSelector);
        
        targets.forEach(target => {
            const text = target.textContent.toLowerCase();
            const shouldShow = text.includes(searchTerm);
            target.style.display = shouldShow ? '' : 'none';
        });
    });
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
    
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Check system health
    checkSystemHealth();
    
    // Set up periodic health checks
    setInterval(checkSystemHealth, 60000); // Every minute
});

// Error handling for global errors
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showNotification('An unexpected error occurred. Please refresh the page.', 'danger');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('A background operation failed. Please check the logs.', 'warning');
});
