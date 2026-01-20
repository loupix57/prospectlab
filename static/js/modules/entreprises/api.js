/**
 * API pour les entreprises
 */

(function(window) {
    'use strict';
    
    const EntreprisesAPI = {
        /**
         * Charge toutes les entreprises
         * @returns {Promise<Array>}
         */
        async loadAll() {
            const response = await fetch('/api/entreprises');
            if (!response.ok) throw new Error('Erreur lors du chargement des entreprises');
            return await response.json();
        },
        
        /**
         * Charge les secteurs disponibles
         * @returns {Promise<Array>}
         */
        async loadSecteurs() {
            const response = await fetch('/api/secteurs');
            if (!response.ok) throw new Error('Erreur lors du chargement des secteurs');
            return await response.json();
        },
        
        /**
         * Charge les détails d'une entreprise
         * @param {number} id
         * @returns {Promise<Object>}
         */
        async loadDetails(id) {
            const response = await fetch(`/api/entreprise/${id}`);
            if (!response.ok) throw new Error('Erreur lors du chargement des détails');
            return await response.json();
        },
        
        /**
         * Toggle le statut favori d'une entreprise
         * @param {number} id
         * @returns {Promise<Object>}
         */
        async toggleFavori(id) {
            const response = await fetch(`/api/entreprise/${id}/favori`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error('Erreur lors de la mise à jour du favori');
            return await response.json();
        },
        
        /**
         * Met à jour les tags d'une entreprise
         * @param {number} id
         * @param {Array<string>} tags
         * @returns {Promise<Object>}
         */
        async updateTags(id, tags) {
            const response = await fetch(`/api/entreprise/${id}/tags`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tags })
            });
            if (!response.ok) throw new Error('Erreur lors de la mise à jour des tags');
            return await response.json();
        },
        
        /**
         * Supprime une entreprise
         * @param {number} id
         * @returns {Promise<void>}
         */
        async delete(id) {
            const response = await fetch(`/api/entreprise/${id}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Erreur lors de la suppression');
        },
        
        /**
         * Charge l'analyse technique
         * @param {number} id
         * @returns {Promise<Object|null>}
         */
        async loadTechnicalAnalysis(id) {
            const response = await fetch(`/api/entreprise/${id}/analyse-technique`);
            if (!response.ok) return null;
            return await response.json();
        },
        
        /**
         * Charge l'analyse OSINT
         * @param {number} id
         * @returns {Promise<Object|null>}
         */
        async loadOSINTAnalysis(id) {
            const response = await fetch(`/api/entreprise/${id}/analyse-osint`);
            if (!response.ok) return null;
            return await response.json();
        },
        
        /**
         * Charge l'analyse Pentest
         * @param {number} id
         * @returns {Promise<Object|null>}
         */
        async loadPentestAnalysis(id) {
            const response = await fetch(`/api/entreprise/${id}/analyse-pentest`);
            if (!response.ok) return null;
            return await response.json();
        },
        
        /**
         * Charge les résultats de scraping
         * @param {number} id
         * @returns {Promise<Array>}
         */
        async loadScrapingResults(id) {
            const response = await fetch(`/api/entreprise/${id}/scrapers`);
            if (!response.ok) return [];
            return await response.json();
        },
        
        /**
         * Lance le scraping
         * @param {number} id
         * @param {string} url
         * @returns {Promise<Object>}
         */
        async launchScraping(id, url) {
            const response = await fetch('/api/scraper/unified', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ entreprise_id: id, url })
            });
            if (!response.ok) throw new Error('Erreur lors du lancement du scraping');
            return await response.json();
        },
        
        /**
         * Exporte les entreprises en CSV
         * @returns {Promise<Blob>}
         */
        async exportCSV() {
            const response = await fetch('/api/entreprises/export');
            if (!response.ok) throw new Error('Erreur lors de l\'export');
            return await response.blob();
        }
    };
    
    // Exposer globalement
    window.EntreprisesAPI = EntreprisesAPI;
})(window);

