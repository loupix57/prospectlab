/**
 * Système de notifications
 */

(function(window) {
    'use strict';
    
    const Notifications = {
        /**
         * Affiche une notification
         * @param {string} message
         * @param {string} type - 'info', 'success', 'error', 'warning'
         */
        show(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                background: ${this.getColor(type)};
                color: white;
                border-radius: 6px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                z-index: 10000;
                animation: slideIn 0.3s ease;
                max-width: 400px;
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        },
        
        /**
         * Retourne la couleur selon le type
         * @param {string} type
         * @returns {string}
         */
        getColor(type) {
            const colors = {
                'info': '#3498db',
                'success': '#27ae60',
                'error': '#e74c3c',
                'warning': '#f39c12'
            };
            return colors[type] || colors.info;
        }
    };
    
    // Exposer globalement
    window.Notifications = Notifications;
})(window);

