/**
 * Chargeur de modules simple avec gestion des dépendances
 */

(function(window) {
    'use strict';
    
    const ModuleLoader = {
        loaded: new Set(),
        loading: new Set(),
        
        /**
         * Charge un module JavaScript
         * @param {string} src - Chemin du fichier
         * @returns {Promise<void>}
         */
        async load(src) {
            // Si déjà chargé, ne rien faire
            if (this.loaded.has(src)) {
                return Promise.resolve();
            }
            
            // Si en cours de chargement, attendre
            if (this.loading.has(src)) {
                return new Promise((resolve) => {
                    const checkInterval = setInterval(() => {
                        if (this.loaded.has(src)) {
                            clearInterval(checkInterval);
                            resolve();
                        }
                    }, 50);
                });
            }
            
            // Marquer comme en cours de chargement
            this.loading.add(src);
            
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = src;
                script.async = false; // Chargement synchrone pour respecter l'ordre
                script.onload = () => {
                    this.loaded.add(src);
                    this.loading.delete(src);
                    resolve();
                };
                script.onerror = () => {
                    this.loading.delete(src);
                    reject(new Error(`Erreur lors du chargement de ${src}`));
                };
                document.head.appendChild(script);
            });
        },
        
        /**
         * Charge plusieurs modules dans l'ordre
         * @param {Array<string>} modules - Liste des chemins
         * @returns {Promise<void>}
         */
        async loadAll(modules) {
            for (const module of modules) {
                await this.load(module);
            }
        }
    };
    
    // Exposer globalement
    window.ModuleLoader = ModuleLoader;
})(window);

