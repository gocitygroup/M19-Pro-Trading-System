/* ========================================
   G-SignalX M19 Trading System
   Theme Management Module
   ======================================== */

/**
 * Apply saved theme early to avoid flash
 * This function should be called inline in <head> before page render
 */
(function applyInitialTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('theme-dark');
    }
})();

/**
 * Theme Manager - Handles theme toggling and persistence
 */
const ThemeManager = {
    /**
     * Initialize theme toggle functionality
     * @param {string} buttonId - ID of the theme toggle button
     */
    init: function(buttonId = 'themeToggle') {
        const themeToggleBtn = document.getElementById(buttonId);
        if (!themeToggleBtn) {
            console.warn(`Theme toggle button with ID "${buttonId}" not found`);
            return;
        }

        // Apply saved theme on load
        const startingTheme = localStorage.getItem('theme') || 'light';
        this.applyTheme(startingTheme, themeToggleBtn);

        // Add click event listener
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.applyTheme(nextTheme, themeToggleBtn);
        });
    },

    /**
     * Apply theme and update button text
     * @param {string} theme - Theme to apply ('light' or 'dark')
     * @param {HTMLElement} button - Theme toggle button element
     */
    applyTheme: function(theme, button = null) {
        const isDark = theme === 'dark';
        
        // Toggle theme class on document root
        document.documentElement.classList.toggle('theme-dark', isDark);
        
        // Save to localStorage
        localStorage.setItem('theme', theme);
        
        // Update button if provided
        if (button) {
            button.innerHTML = isDark 
                ? '<i class="fas fa-sun"></i> Light Mode' 
                : '<i class="fas fa-moon"></i> Dark Mode';
            
            // Update button classes for styling
            button.classList.toggle('btn-outline-light', !isDark);
            button.classList.toggle('btn-outline-secondary', isDark);
        }

        // Dispatch custom event for other components to react to theme change
        const event = new CustomEvent('themeChanged', { detail: { theme } });
        document.dispatchEvent(event);
    },

    /**
     * Get current theme
     * @returns {string} Current theme ('light' or 'dark')
     */
    getCurrentTheme: function() {
        return document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
    },

    /**
     * Toggle theme
     */
    toggleTheme: function() {
        const currentTheme = this.getCurrentTheme();
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(nextTheme);
    }
};

/**
 * Initialize theme on DOM ready
 * Tries common button IDs used across different pages
 */
document.addEventListener('DOMContentLoaded', function() {
    // List of possible theme toggle button IDs
    const possibleButtonIds = [
        'themeToggle',
        'themeToggleSettings',
        'themeToggleManual'
    ];

    // Initialize with the first found button
    for (const buttonId of possibleButtonIds) {
        if (document.getElementById(buttonId)) {
            ThemeManager.init(buttonId);
            break;
        }
    }
});

// Export for use in modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
