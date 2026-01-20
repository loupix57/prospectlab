/**
 * Utilitaires de formatage
 */

(function(window) {
    'use strict';
    
    const Formatters = {
        /**
         * Formate une durée en millisecondes
         * @param {number|null|undefined} ms
         * @returns {string}
         */
        formatMs(ms) {
            if (!ms && ms !== 0) return 'N/A';
            return `${ms} ms`;
        },
        
        /**
         * Formate une taille en bytes
         * @param {number|null|undefined} bytes
         * @returns {string}
         */
        formatBytesShort(bytes) {
            if (!bytes && bytes !== 0) return 'N/A';
            const kb = bytes / 1024;
            if (kb < 1024) return `${kb.toFixed(1)} Ko`;
            return `${(kb / 1024).toFixed(2)} Mo`;
        },
        
        /**
         * Échappe le HTML pour éviter les injections XSS
         * @param {string} text
         * @returns {string}
         */
        escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };
    
    // Exposer globalement
    window.Formatters = Formatters;
})(window);

