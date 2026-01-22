"""
Blueprint pour les routes supplémentaires non encore migrées

Contient les routes pour les emails, templates, scraping et téléchargements.
"""

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
from services.email_sender import EmailSender
from services.template_manager import TemplateManager
from config import EXPORT_FOLDER
from utils.template_helpers import render_page

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
    return render_page('analyse_scraping.html')


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
    
    return render_page('scrape_emails.html')


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
                html_body = None
                if template_id and template:
                    message, is_html = template_manager.render_template(
                        template_id,
                        recipient.get('nom', ''),
                        recipient.get('entreprise', ''),
                        recipient.get('email', ''),
                        recipient.get('entreprise_id')  # Passer l'ID si disponible
                    )
                    if is_html:
                        html_body = message
                        # Pour HTML, créer une version texte simplifiée
                        import re
                        message = re.sub(r'<[^>]+>', '', message)  # Enlever les balises HTML
                        message = re.sub(r'\s+', ' ', message).strip()  # Nettoyer les espaces
                elif custom_message:
                    message = custom_message
                else:
                    return jsonify({'error': 'Template ou message requis'}), 400
                
                # Personnaliser le sujet
                subject_template = subject or (template.get('subject', 'Prospection') if template else 'Prospection')
                try:
                    personalized_subject = subject_template.format(
                        nom=recipient.get('nom', ''),
                        entreprise=recipient.get('entreprise', '')
                    )
                except:
                    personalized_subject = subject_template
                
                # Envoyer l'email
                result = email_sender.send_email(
                    to=recipient['email'],
                    subject=personalized_subject,
                    body=message,
                    recipient_name=recipient.get('nom', ''),
                    html_body=html_body
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
    return render_page('send_emails.html', templates=templates)


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
    return render_page('templates.html', templates=templates)


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

