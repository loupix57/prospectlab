// Gestion des campagnes email

let selectedRecipients = [];
let entreprisesData = [];
let templatesData = [];
let socket = null;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadCampagnes();
    loadTemplates();
    loadEntreprises();
    initWebSocket();
});

// Charger les campagnes
async function loadCampagnes() {
    try {
        const response = await fetch('/api/campagnes');
        const campagnes = await response.json();
        displayCampagnes(campagnes);
    } catch (error) {
        document.getElementById('campagnes-grid').innerHTML =
            '<div class="empty-state"><p>Erreur lors du chargement des campagnes</p></div>';
    }
}

// Afficher les campagnes
function displayCampagnes(campagnes) {
    const grid = document.getElementById('campagnes-grid');

    if (campagnes.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📧</div>
                <h3>Aucune campagne</h3>
                <p>Créez votre première campagne pour commencer</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = campagnes.map(campagne => `
        <div class="campagne-card" data-campagne-id="${campagne.id}">
            <div class="campagne-header">
                <h3 class="campagne-title">${escapeHtml(campagne.nom)}</h3>
                <span class="campagne-statut statut-${campagne.statut}">${campagne.statut}</span>
            </div>
            <div class="campagne-meta">
                <div>Créée le ${formatDate(campagne.date_creation)}</div>
                ${campagne.sujet ? `<div>Sujet: ${escapeHtml(campagne.sujet)}</div>` : ''}
            </div>
            <div class="campagne-stats">
                <div class="stat-item">
                    <div class="stat-value">${campagne.total_destinataires || 0}</div>
                    <div class="stat-label">Destinataires</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${campagne.total_envoyes || 0}</div>
                    <div class="stat-label">Envoyés</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${campagne.total_reussis || 0}</div>
                    <div class="stat-label">Réussis</div>
                </div>
            </div>
            <div class="campagne-actions">
                <button class="btn-action btn-view" onclick="viewCampagne(${campagne.id})">
                    Voir détails
                </button>
                <button class="btn-action btn-delete" onclick="deleteCampagne(${campagne.id})">
                    Supprimer
                </button>
            </div>
            ${campagne.statut === 'running' ? `
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.round((campagne.total_envoyes / Math.max(campagne.total_destinataires, 1)) * 100)}%">                                                                                           
                            ${Math.round((campagne.total_envoyes / Math.max(campagne.total_destinataires, 1)) * 100)}%      
                        </div>
                    </div>
                    <div class="progress-text">Envoi en cours...</div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Charger les templates
async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const allTemplates = await response.json();

        // Filtrer pour ne garder que les templates HTML
        templatesData = allTemplates.filter(t => t.is_html === true);

        const select = document.getElementById('campagne-template');
        select.innerHTML = '<option value="">Aucun (message personnalisé)</option>';
        
        templatesData.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            select.appendChild(option);
        });

        // Écouter les changements de template
        select.addEventListener('change', function() {
            const template = templatesData.find(t => t.id === this.value);
            const messageTextarea = document.getElementById('campagne-message');
            let previewDiv = document.getElementById('template-preview');
            
            if (template) {
                document.getElementById('campagne-sujet').value = template.subject || '';
                
                // Pour les templates HTML, on cache le textarea et on affiche un aperçu
                if (template.is_html) {
                    messageTextarea.style.display = 'none';
                    
                    // Créer l'aperçu si nécessaire
                    if (!previewDiv) {
                        previewDiv = document.createElement('div');
                        previewDiv.id = 'template-preview';
                        previewDiv.className = 'template-preview';
                        messageTextarea.parentNode.insertBefore(previewDiv, messageTextarea.nextSibling);
                    }
                    
                    // Afficher l'aperçu dans un iframe pour un rendu propre
                    previewDiv.style.display = 'block';
                    
                    // Créer l'iframe
                    let iframe = previewDiv.querySelector('iframe');
                    if (!iframe) {
                        iframe = document.createElement('iframe');
                        iframe.style.width = '100%';
                        iframe.style.border = 'none';
                        iframe.style.minHeight = '400px';
                        iframe.style.background = 'white';
                        previewDiv.innerHTML = '';
                        previewDiv.appendChild(iframe);
                    }
                    
                    // Écrire le contenu dans l'iframe
                    try {
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        iframeDoc.open();
                        iframeDoc.write(template.content);
                        iframeDoc.close();
                    } catch (e) {
                        // Fallback : afficher le HTML directement si l'iframe ne fonctionne pas
                        previewDiv.innerHTML = '<div style="padding: 20px; max-height: 400px; overflow-y: auto;">' + template.content + '</div>';
                    }
                } else {
                    messageTextarea.style.display = 'block';
                    messageTextarea.value = template.content || '';
                    if (previewDiv) {
                        previewDiv.style.display = 'none';
                    }
                }
            } else {
                // Aucun template sélectionné
                messageTextarea.style.display = 'block';
                messageTextarea.value = '';
                if (previewDiv) {
                    previewDiv.style.display = 'none';
                }
            }
        });
    } catch (error) {
        // Erreur silencieuse, les templates ne sont pas critiques
    }
}

// Charger les entreprises avec emails
async function loadEntreprises() {
    try {
        const response = await fetch('/api/entreprises/emails');
        entreprisesData = await response.json();
        displayEntreprises();
    } catch (error) {
        document.getElementById('recipients-selector').innerHTML =
            '<div class="empty-state"><p>Erreur lors du chargement des entreprises</p></div>';
    }
}

// Afficher les entreprises
function displayEntreprises() {
    const container = document.getElementById('recipients-selector');

    if (entreprisesData.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>Aucune entreprise avec email disponible</p></div>';
        return;
    }

    container.innerHTML = entreprisesData.map(entreprise => {
        const emails = entreprise.emails || [];
        if (emails.length === 0) return '';

        return `
            <div class="entreprise-item" data-entreprise-id="${entreprise.id}">
                <div class="entreprise-header">
                    <div>
                        <div class="entreprise-name">${escapeHtml(entreprise.nom)}</div>
                        ${entreprise.secteur ? `<div style="font-size: 0.85em; color: #666;">${escapeHtml(entreprise.secteur)}</div>` : ''}                                                                                                             
                    </div>
                    <div class="checkbox-wrapper">
                        <input type="checkbox"
                               id="entreprise-${entreprise.id}"
                               onchange="toggleEntreprise(${entreprise.id}, this.checked)">
                        <label for="entreprise-${entreprise.id}">Tout sélectionner</label>
                    </div>
                </div>
                <div class="emails-list">
                    ${emails.map((email, idx) => `
                        <div class="email-item">
                            <input type="checkbox"
                                   id="email-${entreprise.id}-${idx}"
                                   data-email='${JSON.stringify(email)}'
                                   onchange="toggleEmail(${entreprise.id}, ${idx}, this.checked)">
                            <span class="email-address">${escapeHtml(email.email)}</span>
                            ${email.nom && email.nom !== 'N/A' ? `<span>(${escapeHtml(email.nom)})</span>` : ''}
                            <span class="email-source">${email.source}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).filter(html => html).join('');
}

// Toggle entreprise (sélectionner/désélectionner tous les emails)
function toggleEntreprise(entrepriseId, checked) {
    const entreprise = entreprisesData.find(e => e.id === entrepriseId);
    if (!entreprise) return;

    entreprise.emails.forEach((email, idx) => {
        const checkbox = document.getElementById(`email-${entrepriseId}-${idx}`);
        if (checkbox) {
            checkbox.checked = checked;
            toggleEmail(entrepriseId, idx, checked);
        }
    });

    updateEntrepriseItemStyle(entrepriseId, checked);
}

// Toggle email individuel
function toggleEmail(entrepriseId, emailIdx, checked) {
    const entreprise = entreprisesData.find(e => e.id === entrepriseId);
    if (!entreprise || !entreprise.emails[emailIdx]) return;

    const email = entreprise.emails[emailIdx];
    const emailKey = `${email.email}-${email.entreprise_id}`;

    if (checked) {
        // Ajouter le destinataire
        if (!selectedRecipients.find(r => r.email === email.email && r.entreprise_id === email.entreprise_id)) {
            selectedRecipients.push({
                email: email.email,
                nom: email.nom || null,
                entreprise: entreprise.nom,
                entreprise_id: email.entreprise_id
            });
        }
    } else {
        // Retirer le destinataire
        selectedRecipients = selectedRecipients.filter(
            r => !(r.email === email.email && r.entreprise_id === email.entreprise_id)
        );
    }

    updateSelectedCount();
    updateEntrepriseItemStyle(entrepriseId);
}

// Mettre à jour le style de l'item entreprise
function updateEntrepriseItemStyle(entrepriseId, forceChecked = null) {
    const item = document.querySelector(`.entreprise-item[data-entreprise-id="${entrepriseId}"]`);
    if (!item) return;

    const entreprise = entreprisesData.find(e => e.id === entrepriseId);
    if (!entreprise) return;

    const allChecked = entreprise.emails.every((email, idx) => {
        const checkbox = document.getElementById(`email-${entrepriseId}-${idx}`);
        return checkbox && checkbox.checked;
    });

    const someChecked = entreprise.emails.some((email, idx) => {
        const checkbox = document.getElementById(`email-${entrepriseId}-${idx}`);
        return checkbox && checkbox.checked;
    });

    if (forceChecked !== null) {
        item.classList.toggle('selected', forceChecked);
    } else {
        item.classList.toggle('selected', someChecked);
    }
}

// Mettre à jour le compteur de sélection
function updateSelectedCount() {
    const countDiv = document.getElementById('selected-count');
    const count = selectedRecipients.length;
    
    if (count > 0) {
        countDiv.style.display = 'block';
        countDiv.textContent = `${count} destinataire(s) sélectionné(s)`;
    } else {
        countDiv.style.display = 'none';
    }
}

// Ouvrir le modal de nouvelle campagne
function openNewCampagneModal() {
    selectedRecipients = [];
    document.getElementById('campagne-form').reset();
    document.getElementById('selected-count').style.display = 'none';
    document.getElementById('campagne-modal').style.display = 'block';

    // Décocher toutes les cases
    document.querySelectorAll('#recipients-selector input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });

    document.querySelectorAll('.entreprise-item').forEach(item => {
        item.classList.remove('selected');
    });
}

// Fermer le modal
function closeModal() {
    document.getElementById('campagne-modal').style.display = 'none';
}

// Soumettre la campagne
// Générer un nom de campagne automatique
function generateCampagneName(templateName, recipientCount) {
    const now = new Date();
    const dateStr = now.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
    const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    
    // Noms courts et originaux
    const prefixes = ['📧', '🚀', '⚡', '🎯', '💼', '📬', '✨', '🔥'];
    const randomPrefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    
    // Nom du template (raccourci)
    let templatePart = '';
    if (templateName) {
        // Extraire un mot clé du nom du template
        const keywords = {
            'modernisation': 'Mod',
            'optimisation': 'Opt',
            'sécurité': 'Sec',
            'présence': 'Pres',
            'audit': 'Audit'
        };
        for (const [key, val] of Object.entries(keywords)) {
            if (templateName.toLowerCase().includes(key)) {
                templatePart = val;
                break;
            }
        }
        if (!templatePart) {
            templatePart = templateName.substring(0, 4).toUpperCase();
        }
    }
    
    // Construire le nom
    const parts = [
        randomPrefix,
        dateStr.replace(/\//g, '.'),
        timeStr.replace(':', 'h'),
        templatePart ? `-${templatePart}` : '',
        recipientCount > 0 ? `(${recipientCount})` : ''
    ].filter(p => p !== '');
    
    return parts.join(' ');
}

async function submitCampagne() {
    const form = document.getElementById('campagne-form');
    const formData = new FormData(form);

    const templateId = formData.get('template_id') || null;
    const sujet = formData.get('sujet');
    const customMessage = formData.get('custom_message') || null;
    const delay = parseInt(formData.get('delay')) || 2;

    if (!sujet) {
        alert('Veuillez remplir le sujet de l\'email');
        return;
    }

    // Générer automatiquement le nom de la campagne
    const template = templatesData.find(t => t.id === templateId);
    const templateName = template ? template.name : null;
    const nom = generateCampagneName(templateName, selectedRecipients.length);

    if (selectedRecipients.length === 0) {
        alert('Veuillez sélectionner au moins un destinataire');
        return;
    }

    if (!templateId && !customMessage) {
        alert('Veuillez sélectionner un modèle ou saisir un message personnalisé');
        return;
    }

    const submitBtn = document.querySelector('.btn-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Création en cours...';
    
    try {
        const response = await fetch('/api/campagnes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nom,
                template_id: templateId,
                sujet,
                recipients: selectedRecipients,
                custom_message: customMessage,
                delay
            })
        });

        const data = await response.json();

        if (data.success) {
            closeModal();
            loadCampagnes();

            // Démarrer le monitoring WebSocket
            if (socket && socket.connected) {
                socket.emit('monitor_campagne', {
                    task_id: data.task_id,
                    campagne_id: data.campagne_id
                });
            }

            // alert('Campagne créée avec succès ! L\'envoi est en cours...');
        } else {
            alert('Erreur: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        alert('Erreur lors de la création de la campagne');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Lancer la campagne';
    }
}

// Voir les détails d'une campagne
async function viewCampagne(campagneId) {
    try {
        const response = await fetch(`/api/campagnes/${campagneId}`);
        const campagne = await response.json();

        // Ouvrir la modale de résultats avec le nom de la campagne
        openResultsModal(campagneId, campagne.nom);
    } catch (error) {
        alert('Erreur lors du chargement des détails');
    }
}

// Ouvrir la modale de résultats
function openResultsModal(campagneId, campagneName) {
    const modal = document.getElementById('results-modal');
    const campagneNameEl = document.getElementById('results-campagne-name');
    const body = document.getElementById('results-modal-body');

    if (campagneNameEl) {
        campagneNameEl.textContent = campagneName || `Campagne #${campagneId}`;
    }

    // Afficher le loading
    body.innerHTML = `
        <div class="results-loading">
            <div class="loading-spinner"></div>
            <p>Chargement des résultats...</p>
        </div>
    `;

    modal.classList.add('show');

    // Charger les statistiques
    loadCampagneResults(campagneId);
}

// Fermer la modale de résultats
function closeResultsModal() {
    const modal = document.getElementById('results-modal');
    modal.classList.remove('show');
}

// Charger les résultats de la campagne
async function loadCampagneResults(campagneId) {
    try {
        const response = await fetch(`/api/tracking/campagne/${campagneId}`);
        const stats = await response.json();

        displayCampagneResults(stats);
    } catch (error) {
        const body = document.getElementById('results-modal-body');
        body.innerHTML = `
            <div class="results-loading">
                <p style="color: #e74c3c;">Erreur lors du chargement des résultats</p>
            </div>
        `;
    }
}

// Afficher les résultats de la campagne
function displayCampagneResults(stats) {
    const body = document.getElementById('results-modal-body');

    const openRate = stats.open_rate ? stats.open_rate.toFixed(1) : '0.0';
    const clickRate = stats.click_rate ? stats.click_rate.toFixed(1) : '0.0';
    const avgReadTime = stats.avg_read_time ? Math.round(stats.avg_read_time) : 'N/A';

    // Fonction pour obtenir le badge de statut
    function getStatusBadge(statut, hasOpened, hasClicked) {
        if (statut === 'failed') {
            return '<span class="status-badge status-failed">Échec</span>';
        }
        if (hasClicked) {
            return '<span class="status-badge status-clicked">Clic</span>';
        }
        if (hasOpened) {
            return '<span class="status-badge status-opened">Ouvert</span>';
        }
        return '<span class="status-badge status-sent">Envoyé</span>';
    }

    // Tableau des emails
    let emailsTable = '';
    if (stats.emails && stats.emails.length > 0) {
        emailsTable = `
            <div class="results-section">
                <h3 class="results-section-title">Détails par contact (${stats.emails.length})</h3>
                <div class="results-table-container">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Contact</th>
                                <th>Entreprise</th>
                                <th class="text-center">Statut</th>
                                <th class="text-center">Ouvertures</th>
                                <th class="text-center">Clics</th>
                                <th>Date envoi</th>
                                <th>Dernière ouverture</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stats.emails.map(email => `
                                <tr class="${email.has_clicked ? 'row-clicked' : email.has_opened ? 'row-opened' : ''}">    
                                    <td>
                                        <div class="contact-name">${formatContactName(email.nom_destinataire)}</div>      
                                        <div class="contact-email">${escapeHtml(email.email)}</div>
                                    </td>
                                    <td>${escapeHtml(email.entreprise || 'N/A')}</td>
                                    <td class="text-center">${getStatusBadge(email.statut, email.has_opened, email.has_clicked)}</td>                                                                                                                   
                                    <td class="text-center">
                                        ${email.opens > 0 ? `<span class="stat-value stat-opens">${email.opens}</span>` : '<span class="stat-value stat-zero">0</span>'}                                                                                
                                    </td>
                                    <td class="text-center">
                                        ${email.clicks > 0 ? `<span class="stat-value stat-clicks">${email.clicks}</span>` : '<span class="stat-value stat-zero">0</span>'}                                                                             
                                    </td>
                                    <td class="text-muted">${formatDate(email.date_envoi)}</td>
                                    <td class="text-muted">${formatDate(email.last_open)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    body.innerHTML = `
        <div class="results-content">
            <h2 class="results-main-title">Statistiques de prospection</h2>

            <!-- Vue d'ensemble -->
            <div class="results-stats-grid">
                <div class="stat-card stat-primary">
                    <div class="stat-value-large">${stats.total_emails || 0}</div>
                    <div class="stat-label">Emails envoyés</div>
                </div>
                <div class="stat-card stat-info">
                    <div class="stat-value-large">${stats.total_opens || 0}</div>
                    <div class="stat-label">Ouvertures</div>
                    <div class="stat-sublabel">${openRate}% du total</div>
                </div>
                <div class="stat-card stat-success">
                    <div class="stat-value-large">${stats.total_clicks || 0}</div>
                    <div class="stat-label">Clics</div>
                    <div class="stat-sublabel">${clickRate}% du total</div>
                </div>
                <div class="stat-card stat-warning">
                    <div class="stat-value-large">${openRate}%</div>
                    <div class="stat-label">Taux d'ouverture</div>
                </div>
            </div>

            <!-- Indicateurs de performance -->
            <div class="results-performance-grid">
                <div class="performance-card">
                    <div class="performance-icon">📈</div>
                    <div class="performance-content">
                        <div class="performance-label">Taux de clic</div>
                        <div class="performance-value">${clickRate}%</div>
                    </div>
                </div>
                <div class="performance-card">
                    <div class="performance-icon">⏱</div>
                    <div class="performance-content">
                        <div class="performance-label">Temps de lecture moyen</div>
                        <div class="performance-value">${avgReadTime}s</div>
                    </div>
                </div>
            </div>

            ${emailsTable}
        </div>
    `;
}

// Fermer la modale en cliquant en dehors
document.addEventListener('click', function(event) {
    const modal = document.getElementById('results-modal');
    if (event.target === modal) {
        closeResultsModal();
    }
});

// Supprimer une campagne
async function deleteCampagne(campagneId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette campagne ?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/campagnes/${campagneId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadCampagnes();
        } else {
            alert('Erreur lors de la suppression');
        }
    } catch (error) {
        alert('Erreur lors de la suppression');
    }
}

// Initialiser WebSocket pour le suivi en temps réel
function initWebSocket() {
    if (typeof io === 'undefined') {
        return;
    }
    
    socket = io();

    socket.on('connect', function() {
        // Connexion WebSocket établie
    });

    socket.on('campagne_progress', function(data) {
        updateCampagneProgress(data);
    });

    socket.on('campagne_complete', function(data) {
        updateCampagneProgress({
            campagne_id: data.campagne_id,
            progress: 100,
            current: data.result?.total || 0,
            total: data.result?.total || 0,
            sent: data.result?.total_sent || 0,
            failed: data.result?.total_failed || 0,
            message: 'Terminé'
        });

        // Recharger pour mettre à jour le statut
        loadCampagnes();

        // Afficher une notification de succès
        const totalSent = data.result?.total_sent || 0;
        const totalFailed = data.result?.total_failed || 0;
        showNotification(`Campagne terminée ! ${totalSent} emails envoyés${totalFailed > 0 ? `, ${totalFailed} échecs` : ''}`, 'success');                                                                                                              
    });

    socket.on('campagne_error', function(data) {
        // Mettre à jour l'affichage pour montrer l'erreur
        const card = document.querySelector(`[data-campagne-id="${data.campagne_id}"]`);
        if (card) {
            const progressContainer = card.querySelector('.progress-bar-container');
            if (progressContainer) {
                progressContainer.innerHTML = `
                    <div class="error-message" style="color: #dc3545; padding: 8px; background: #f8d7da; border-radius: 4px; margin-top: 8px;">                                                                                                         
                        ❌ Erreur: ${escapeHtml(data.error || 'Erreur inconnue')}
                    </div>
                `;
            }
        }
        // Recharger pour mettre à jour le statut
        loadCampagnes();
        showNotification('Erreur lors de l\'envoi de la campagne: ' + (data.error || 'Erreur inconnue'), 'error');
    });
}

// Mettre à jour la progression d'une campagne en temps réel
function updateCampagneProgress(data) {
    const campagneId = data.campagne_id;
    const progress = data.progress || 0;
    const current = data.current || 0;
    const total = data.total || 0;
    const sent = data.sent || 0;
    const failed = data.failed || 0;
    const message = data.message || 'Envoi en cours...';

    // Trouver la carte de campagne correspondante
    const card = document.querySelector(`[data-campagne-id="${campagneId}"]`);
    if (!card) {
        // Si la carte n'existe pas, recharger les campagnes
        loadCampagnes();
        return;
    }

    // Mettre à jour les stats
    const statItems = card.querySelectorAll('.stat-item');
    if (statItems.length >= 3) {
        // Destinataires
        statItems[0].querySelector('.stat-value').textContent = total;
        // Envoyés
        statItems[1].querySelector('.stat-value').textContent = sent;
        // Réussis
        statItems[2].querySelector('.stat-value').textContent = sent - failed;
    }

    // Mettre à jour la barre de progression
    let progressContainer = card.querySelector('.progress-bar-container');
    if (!progressContainer) {
        // Créer le conteneur de progression s'il n'existe pas
        const actionsDiv = card.querySelector('.campagne-actions');
        if (actionsDiv) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'progress-bar-container';
            actionsDiv.parentNode.insertBefore(progressContainer, actionsDiv.nextSibling);
        } else {
            return;
        }
    }

    // Construire un message propre
    let progressMessage;
    if (message && message.trim() !== '') {
        // Utiliser le message du backend tel quel
        progressMessage = message;
    } else if (current > 0 && total > 0) {
        // Construire un message si aucun n'est fourni
        progressMessage = `Envoi ${current}/${total}`;
    } else {
        progressMessage = 'Envoi en cours...';
    }
    
    // S'assurer que le message n'est jamais vide
    if (!progressMessage || progressMessage.trim() === '') {
        progressMessage = `Envoi ${current || 0}/${total || 0}`;
    }
    
    // Créer les éléments séparément pour s'assurer qu'ils sont bien insérés
    progressContainer.innerHTML = `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress}%">
                ${progress}%
            </div>
        </div>
    `;
    
    // Ajouter le texte dans un élément séparé pour forcer l'affichage
    const textElement = document.createElement('div');
    textElement.className = 'progress-text';
    textElement.style.cssText = 'color: #333 !important; display: block !important; visibility: visible !important; opacity: 1 !important; text-align: center; margin-top: 10px; padding: 5px; font-size: 0.9em; line-height: 1.4;';
    textElement.textContent = progressMessage;
    progressContainer.appendChild(textElement);

    // Mettre à jour le statut si nécessaire
    const statutBadge = card.querySelector('.campagne-statut');
    if (statutBadge && progress < 100) {
        statutBadge.textContent = 'running';
        statutBadge.className = 'campagne-statut statut-running';
    }
}

// Afficher une notification
function showNotification(message, type = 'info') {
    // Créer un élément de notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#bee5eb'};
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Supprimer après 5 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Ajouter les styles d'animation si pas déjà présents
if (!document.getElementById('notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Utilitaires
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatContactName(nomDestinataire) {
    if (!nomDestinataire || nomDestinataire === 'N/A') return 'N/A';
    
    // Si c'est déjà formaté (pas de JSON), retourner tel quel
    if (!nomDestinataire.startsWith('{') && !nomDestinataire.startsWith('[')) {
        return escapeHtml(nomDestinataire);
    }
    
    // Si c'est une chaîne JSON, essayer de la parser
    try {
        const parsed = JSON.parse(nomDestinataire);
        if (parsed && typeof parsed === 'object') {
            if (parsed.full_name) {
                return escapeHtml(parsed.full_name);
            }
            if (parsed.first_name || parsed.last_name) {
                const parts = [parsed.first_name, parsed.last_name].filter(Boolean);
                return escapeHtml(parts.join(' ') || 'N/A');
            }
        }
    } catch (e) {
        // Si le parsing échoue, retourner tel quel
    }
    
    // Sinon, retourner tel quel
    return escapeHtml(nomDestinataire);
}

