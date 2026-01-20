/**
 * Fonction debounce pour limiter les appels de fonction
 */

(function(window) {
    'use strict';
    
    /**
     * Crée une fonction debounced
     * @param {Function} func - Fonction à débouncer
     * @param {number} wait - Délai en millisecondes
     * @returns {Function}
     */
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
    
    // Exposer globalement
    window.debounce = debounce;
})(window);

