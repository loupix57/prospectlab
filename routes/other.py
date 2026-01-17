"""
Blueprint pour les routes supplémentaires non encore migrées

Contient les routes pour les emails, templates, scraping et téléchargements.
"""

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash, Response
import os
from services.email_sender import EmailSender
from services.template_manager import TemplateManager
from services.database import Database
from config import EXPORT_FOLDER
from datetime import datetime
import time

other_bp = Blueprint('other', __name__)

# Initialiser les services
template_manager = TemplateManager()


@other_bp.route('/analyse/scraping')
def analyse_scraping_page():
    """
    Page d'analyse/scraping unifiée
    
    Returns:
        str: Template HTML de la page d'analyse/scraping
    """
    return render_template('analyse_scraping.html')


@other_bp.route('/scrape-emails', methods=['GET', 'POST'])
def scrape_emails():
    """
    Scrape les emails d'un site web (route HTTP pour compatibilité)
    
    Methods:
        GET: Affiche le formulaire de scraping
        POST: Retourne un message indiquant d'utiliser WebSocket
        
    Returns:
        str ou JSON: Template HTML ou message JSON
    """
    if request.method == 'POST':
        return jsonify({
            'message': 'Utilisez WebSocket pour les mises à jour en temps réel',
            'use_websocket': True
        }), 200
    
    return render_template('scrape_emails.html')


@other_bp.route('/send-emails', methods=['GET', 'POST'])
def send_emails():
    """
    Envoi d'emails de prospection
    
    Methods:
        GET: Affiche le formulaire d'envoi
        POST: Envoie les emails
        
    Returns:
        str ou JSON: Template HTML ou résultats JSON
    """
    if request.method == 'POST':
        data = request.get_json()
        
        # Récupérer les données
        recipients = data.get('recipients', [])  # Liste de {email, nom, entreprise}
        template_id = data.get('template_id')
        subject = data.get('subject')
        custom_message = data.get('custom_message')
        
        if not recipients:
            return jsonify({'error': 'Aucun destinataire'}), 400
        
        try:
            email_sender = EmailSender()
            
            # Charger le template si fourni
            template = None
            if template_id:
                template = template_manager.get_template(template_id)
                if not template:
                    return jsonify({'error': 'Template introuvable'}), 404
            
            results = []
            for recipient in recipients:
                # Personnaliser le message
                if template_id and template:
                    message = template_manager.render_template(
                        template_id,
                        recipient.get('nom', ''),
                        recipient.get('entreprise', ''),
                        recipient.get('email', '')
                    )
                elif custom_message:
                    message = custom_message
                else:
                    return jsonify({'error': 'Template ou message requis'}), 400
                
                # Envoyer l'email
                result = email_sender.send_email(
                    to=recipient['email'],
                    subject=subject or (template.get('subject', 'Prospection') if template else 'Prospection'),
                    body=message,
                    recipient_name=recipient.get('nom', '')
                )
                
                results.append({
                    'email': recipient['email'],
                    'success': result['success'],
                    'message': result.get('message', '')
                })
            
            return jsonify({
                'success': True,
                'results': results,
                'total_sent': sum(1 for r in results if r['success']),
                'total_failed': sum(1 for r in results if not r['success'])
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET: Afficher le formulaire
    templates = template_manager.list_templates()
    return render_template('send_emails.html', templates=templates)


@other_bp.route('/templates', methods=['GET', 'POST'])
def manage_templates():
    """
    Gestion des modèles de messages
    
    Methods:
        GET: Affiche la liste des templates
        POST: Crée, modifie ou supprime un template
        
    Returns:
        str ou JSON: Template HTML ou résultats JSON
    """
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'create':
            template = template_manager.create_template(
                name=data.get('name'),
                subject=data.get('subject'),
                content=data.get('content'),
                category=data.get('category', 'cold_email')
            )
            return jsonify({'success': True, 'template': template})
        
        elif action == 'update':
            template = template_manager.update_template(
                template_id=data.get('template_id'),
                name=data.get('name'),
                subject=data.get('subject'),
                content=data.get('content')
            )
            return jsonify({'success': True, 'template': template})
        
        elif action == 'delete':
            template_manager.delete_template(data.get('template_id'))
            return jsonify({'success': True})
    
    # GET: Liste des templates
    templates = template_manager.list_templates()
    return render_template('templates.html', templates=templates)


@other_bp.route('/download/<filename>')
def download_file(filename):
    """
    Télécharger un fichier exporté
    
    Args:
        filename (str): Nom du fichier à télécharger
        
    Returns:
        Response: Fichier en téléchargement ou redirection avec message d'erreur
    """
    from flask import render_template
    
    filepath = os.path.join(EXPORT_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        # Fichier introuvable - afficher une page d'erreur avec message clair
        flash('Le fichier exporté n\'existe plus. Il a peut-être été supprimé automatiquement après 6 heures.', 'error')
        return render_template('error.html', 
                             error_title='Fichier introuvable',
                             error_message=f'Le fichier "{filename}" n\'a pas été trouvé dans les exports.',
                             error_details='Les fichiers exportés sont automatiquement supprimés après 6 heures pour libérer de l\'espace. Veuillez relancer l\'analyse pour générer un nouvel export.',
                             back_url=url_for('main.index'))


@other_bp.route('/api/templates')
def api_templates():
    """
    API: Liste des templates
    
    Returns:
        JSON: Liste des templates
    """
    templates = template_manager.list_templates()
    return jsonify(templates)


@other_bp.route('/api/templates/<template_id>')
def api_template_detail(template_id):
    """
    API: Détails d'un template
    
    Args:
        template_id (str): ID du template
        
    Returns:
        JSON: Détails du template ou erreur 404
    """
    template = template_manager.get_template(template_id)
    if template:
        return jsonify(template)
    return jsonify({'error': 'Template introuvable'}), 404


# ==================== ROUTES POUR LES CAMPAGNES EMAIL ====================

@other_bp.route('/campagnes', methods=['GET'])
def list_campagnes():
    """
    Liste toutes les campagnes email
    
    Returns:
        str: Template HTML de la liste des campagnes
    """
    from services.database import Database
    db = Database()
    campagnes = db.list_campagnes(limit=100)
    return render_template('campagnes.html', campagnes=campagnes)


@other_bp.route('/api/campagnes', methods=['GET'])
def api_list_campagnes():
    """
    API: Liste des campagnes
    
    Returns:
        JSON: Liste des campagnes
    """
    from services.database import Database
    db = Database()
    statut = request.args.get('statut')
    campagnes = db.list_campagnes(statut=statut, limit=100)
    return jsonify(campagnes)


@other_bp.route('/api/campagnes', methods=['POST'])
def api_create_campagne():
    """
    API: Crée une nouvelle campagne
    
    Returns:
        JSON: Campagne créée
    """
    from services.database import Database
    from tasks.email_tasks import send_campagne_task
    
    data = request.get_json()
    
    nom = data.get('nom')
    template_id = data.get('template_id')
    sujet = data.get('sujet')
    recipients = data.get('recipients', [])
    custom_message = data.get('custom_message')
    delay = data.get('delay', 2)
    
    if not nom:
        return jsonify({'error': 'Le nom de la campagne est requis'}), 400
    
    if not recipients:
        return jsonify({'error': 'Aucun destinataire fourni'}), 400
    
    db = Database()
    
    # Créer la campagne
    campagne_id = db.create_campagne(
        nom=nom,
        template_id=template_id,
        sujet=sujet,
        total_destinataires=len(recipients),
        statut='draft'
    )
    
    # Lancer la tâche Celery
    task = send_campagne_task.delay(
        campagne_id=campagne_id,
        recipients=recipients,
        template_id=template_id,
        subject=sujet,
        custom_message=custom_message,
        delay=delay
    )
    
    # Mettre à jour le statut de la campagne
    db.update_campagne(campagne_id, statut='scheduled')
    
    return jsonify({
        'success': True,
        'campagne_id': campagne_id,
        'task_id': task.id
    })


@other_bp.route('/api/campagnes/<int:campagne_id>', methods=['GET'])
def api_get_campagne(campagne_id):
    """
    API: Détails d'une campagne
    
    Args:
        campagne_id: ID de la campagne
    
    Returns:
        JSON: Détails de la campagne
    """
    from services.database import Database
    db = Database()
    campagne = db.get_campagne(campagne_id)
    
    if not campagne:
        return jsonify({'error': 'Campagne introuvable'}), 404
    
    # Récupérer les emails de la campagne
    emails = db.get_emails_campagne(campagne_id)
    campagne['emails'] = emails
    
    return jsonify(campagne)


@other_bp.route('/api/campagnes/<int:campagne_id>', methods=['DELETE'])
def api_delete_campagne(campagne_id):
    """
    API: Supprime une campagne
    
    Args:
        campagne_id: ID de la campagne
    
    Returns:
        JSON: Résultat de la suppression
    """
    from services.database import Database
    import sqlite3
    
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Supprimer la campagne (les emails seront supprimés en cascade)
    cursor.execute('DELETE FROM campagnes_email WHERE id = ?', (campagne_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    if deleted:
        return jsonify({'success': True})
    return jsonify({'error': 'Campagne introuvable'}), 404


@other_bp.route('/api/entreprises/emails', methods=['GET'])
def api_get_entreprises_with_emails():
    """
    API: Récupère les entreprises avec leurs emails disponibles
    
    Returns:
        JSON: Liste des entreprises avec emails
    """
    from services.database import Database
    db = Database()
    entreprises = db.get_entreprises_with_emails(limit=1000)
    return jsonify(entreprises)


# ==================== ROUTES POUR LE TRACKING EMAIL ====================

@other_bp.route('/track/pixel/<tracking_token>')
def track_email_open(tracking_token):
    """
    Pixel de tracking pour détecter l'ouverture de l'email
    
    Args:
        tracking_token: Token de tracking unique
    
    Returns:
        Response: Image 1x1 transparente
    """
    db = Database()
    
    # Récupérer l'IP et le user agent
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Enregistrer l'événement d'ouverture
    db.save_tracking_event(
        tracking_token=tracking_token,
        event_type='open',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Retourner une image 1x1 transparente (GIF)
    # Pixel transparent en base64
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
    
    response = Response(pixel, mimetype='image/gif')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


@other_bp.route('/track/click/<tracking_token>')
def track_email_click(tracking_token):
    """
    Redirection trackée pour les clics sur les liens
    
    Args:
        tracking_token: Token de tracking unique
    
    Returns:
        Response: Redirection vers l'URL originale
    """
    db = Database()
    
    # Récupérer l'URL de destination
    target_url = request.args.get('url')
    
    if not target_url:
        return redirect(url_for('main.index'), code=302)
    
    # Décoder l'URL
    from urllib.parse import unquote
    target_url = unquote(target_url)
    
    # Récupérer l'IP et le user agent
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Enregistrer l'événement de clic
    import json
    event_data = json.dumps({'url': target_url})
    db.save_tracking_event(
        tracking_token=tracking_token,
        event_type='click',
        event_data=event_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Rediriger vers l'URL originale
    return redirect(target_url, code=302)


@other_bp.route('/api/tracking/email/<int:email_id>', methods=['GET'])
def api_get_email_tracking(email_id):
    """
    API: Récupère les statistiques de tracking d'un email
    
    Args:
        email_id: ID de l'email
    
    Returns:
        JSON: Statistiques de tracking
    """
    db = Database()
    stats = db.get_email_tracking_stats(email_id)
    return jsonify(stats)


@other_bp.route('/api/tracking/campagne/<int:campagne_id>', methods=['GET'])
def api_get_campagne_tracking(campagne_id):
    """
    API: Récupère les statistiques de tracking d'une campagne
    
    Args:
        campagne_id: ID de la campagne
    
    Returns:
        JSON: Statistiques agrégées de la campagne
    """
    db = Database()
    stats = db.get_campagne_tracking_stats(campagne_id)
    return jsonify(stats)

