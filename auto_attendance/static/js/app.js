/* =====================================================================
   AutoAttendance Web UI - Main Application Logic
   ===================================================================== */

/**
 * Initialize application on page load
 */
document.addEventListener('DOMContentLoaded', function () {
    console.log('AutoAttendance UI loaded');
    initApp();
});

/**
 * Initialize app
 */
function initApp() {
    // Setup event listeners
    setupEventListeners();

    // Setup range input displays
    setupRangeInputs();

    // Load user preferences
    loadUserPreferences();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Modal close button
    const modalCloseBtn = document.querySelector('.modal-close');
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }

    // Modal click outside to close
    const modal = document.getElementById('modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Range inputs
    document.querySelectorAll('.form-range').forEach(input => {
        input.addEventListener('input', updateRangeDisplay);
    });

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(performSearch, 300));
    }
}

/**
 * Setup range input displays
 */
function setupRangeInputs() {
    document.querySelectorAll('.form-range').forEach(input => {
        const display = input.nextElementSibling;
        if (display && display.classList.contains('range-value')) {
            display.textContent = input.value;
        }
    });
}

/**
 * Update range display
 */
function updateRangeDisplay(e) {
    const display = e.target.nextElementSibling;
    if (display && display.classList.contains('range-value')) {
        display.textContent = e.target.value;
    }
}

/**
 * Perform search
 */
function performSearch(e) {
    const query = e.target.value.toLowerCase();
    console.log('Searching for:', query);

    // This would filter content based on search query
}

/**
 * Load user preferences from localStorage
 */
function loadUserPreferences() {
    const theme = storage.get('theme', 'light');
    const sidebar = storage.get('sidebarCollapsed', false);

    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    if (sidebar) {
        const sidebarEl = document.querySelector('.sidebar');
        if (sidebarEl) {
            sidebarEl.classList.add('collapsed');
        }
    }
}

/**
 * Save user preferences
 */
function saveUserPreferences() {
    const theme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
    const sidebar = document.querySelector('.sidebar').classList.contains('collapsed');

    storage.set('theme', theme);
    storage.set('sidebarCollapsed', sidebar);
}

/**
 * Toggle theme
 */
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    saveUserPreferences();
}

/**
 * Toggle sidebar
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
    saveUserPreferences();
}

/**
 * Format timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const today = new Date();

    if (date.toDateString() === today.toDateString()) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } else {
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

/**
 * Highlight code block
 */
function highlightCode(code, language = 'javascript') {
    // Simple syntax highlighting (can be enhanced with highlight.js)
    return code;
}

/**
 * Handle keyboard shortcuts
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) searchInput.focus();
    }

    // Escape: Close modal
    if (e.key === 'Escape') {
        closeModal();
    }
});

/**
 * Update page title
 */
function setPageTitle(title) {
    document.title = `${title} - AutoAttendance`;
}

/**
 * Get system status
 */
async function getSystemStatus() {
    try {
        const response = await apiRequest('/api/stats');
        return response;
    } catch (error) {
        console.error('Error getting system status:', error);
        return null;
    }
}

/**
 * Handle network errors
 */
window.addEventListener('offline', () => {
    showToast('You are offline', 'warning');
});

window.addEventListener('online', () => {
    showToast('You are back online', 'success');
});

/**
 * Enable auto-refresh for dashboard
 */
let autoRefreshInterval = null;

function startAutoRefresh(callback, interval = 5000) {
    autoRefreshInterval = setInterval(callback, interval);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

/**
 * Handle page visibility changes
 */
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        // Resume auto-refresh
        console.log('Page is now visible');
    }
});

/**
 * Async data table functionality
 */
class DataTable {
    constructor(tableSelector, options = {}) {
        this.table = document.querySelector(tableSelector);
        this.tbody = this.table?.querySelector('tbody');
        this.options = {
            sortable: true,
            filterable: true,
            pageable: true,
            pageSize: 10,
            ...options
        };
        this.data = [];
        this.currentPage = 1;
    }

    loadData(data) {
        this.data = data;
        this.render();
    }

    render() {
        if (!this.tbody) return;

        const start = (this.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        const pageData = this.data.slice(start, end);

        this.tbody.innerHTML = pageData.map((row, i) => `
            <tr data-index="${start + i}">
                ${Object.values(row).map(val => `<td>${val}</td>`).join('')}
            </tr>
        `).join('');
    }

    sort(column, order = 'asc') {
        this.data.sort((a, b) => {
            if (order === 'asc') {
                return a[column] > b[column] ? 1 : -1;
            } else {
                return a[column] < b[column] ? 1 : -1;
            }
        });
        this.render();
    }

    filter(predicate) {
        this.data = this.data.filter(predicate);
        this.currentPage = 1;
        this.render();
    }

    nextPage() {
        this.currentPage++;
        this.render();
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.render();
        }
    }
}

/**
 * Form validation
 */
class FormValidator {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        this.errors = {};
    }

    validate() {
        this.errors = {};
        const formData = new FormData(this.form);

        for (let [name, value] of formData) {
            const input = this.form.querySelector(`[name="${name}"]`);
            if (input.required && !value.trim()) {
                this.errors[name] = `${name} is required`;
            }

            if (input.type === 'email' && value && !validateEmail(value)) {
                this.errors[name] = `${name} is not a valid email`;
            }

            if (input.type === 'tel' && value && !validatePhone(value)) {
                this.errors[name] = `${name} is not a valid phone`;
            }

            if (input.dataset.minLength && value.length < input.dataset.minLength) {
                this.errors[name] = `${name} must be at least ${input.dataset.minLength} characters`;
            }
        }

        return Object.keys(this.errors).length === 0;
    }

    displayErrors() {
        // Clear previous errors
        this.form.querySelectorAll('.form-error').forEach(el => el.remove());

        // Show new errors
        for (let [name, message] of Object.entries(this.errors)) {
            const input = this.form.querySelector(`[name="${name}"]`);
            if (input) {
                const error = createElement('div', 'form-error', message);
                input.parentNode.insertBefore(error, input.nextSibling);
            }
        }
    }

    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        for (let [key, value] of formData) {
            data[key] = value;
        }
        return data;
    }
}

/**
 * Initialize animations
 */
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
}

// Call animation init
initAnimations();

/**
 * Performance monitoring
 */
window.addEventListener('load', () => {
    const perfData = window.performance.timing;
    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
    console.log(`Page load time: ${pageLoadTime}ms`);
});

/**
 * Console logging for debugging
 */
const log = {
    info: (msg) => console.log(`[INFO] ${msg}`),
    warn: (msg) => console.warn(`[WARN] ${msg}`),
    error: (msg) => console.error(`[ERROR] ${msg}`),
    debug: (msg) => console.debug(`[DEBUG] ${msg}`)
};
