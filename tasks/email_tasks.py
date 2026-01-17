"""
Tâches Celery pour les services email (analyse et envoi)

Ces tâches enveloppent EmailAnalyzer et EmailSender pour exécuter
les opérations en arrière-plan.
"""

from celery_app import celery
from services.email_analyzer import EmailAnalyzer
from services.email_sender import EmailSender
from services.email_tracker import EmailTracker
from services.logging_config import setup_logger
import logging

# Configurer le logger pour cette tâche
logger = setup_logger(__name__, 'email_tasks.log', level=logging.DEBUG)


@celery.task(bind=True)
def analyze_emails_task(self, emails, source_url=None):
    """
    Analyse une liste d'emails en tâche asynchrone.

    Args:
        self: Instance de la tâche Celery (bind=True)
        emails (list[str]): Liste d'adresses email à analyser
        source_url (str, optional): URL source d'où proviennent les emails

    Returns:
        dict: Résultats avec la liste analysée
    """
    try:
        if not emails:
            return {'success': True, 'results': []}

        analyzer = EmailAnalyzer()
        results = []

        total = len(emails)
        for idx, email in enumerate(emails, start=1):
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': int(idx / total * 100),
                    'message': f'Analyse de {email} ({idx}/{total})'
                }
            )
            analysis = analyzer.analyze_email(email, source_url=source_url)
            if analysis:
                results.append(analysis)

        return {'success': True, 'results': results, 'total': total}
    except Exception as e:
        logger.error(f'Erreur analyse emails: {e}', exc_info=True)
        raise


@celery.task(bind=True)
def send_email_task(self, to, subject, body, recipient_name=None, html_body=None):
    """
    Envoie un email individuel via EmailSender.
    """
    try:
        sender = EmailSender()
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'Préparation de l\'email...'})
        result = sender.send_email(to=to, subject=subject, body=body, recipient_name=recipient_name, html_body=html_body)
        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': 'Email envoyé'})
        return result
    except Exception as e:
        logger.error(f'Erreur envoi email: {e}', exc_info=True)
        raise


@celery.task(bind=True)
def send_bulk_emails_task(self, recipients, subject_template, body_template, delay=2):
    """
    Envoie un lot d'emails avec personnalisation simple.

    Args:
        recipients (list[dict]): {email, nom, entreprise}
        subject_template (str): Sujet avec placeholders {nom}, {entreprise}
        body_template (str): Corps texte avec placeholders {nom}, {entreprise}
        delay (int): Délai entre envois
    """
    try:
        sender = EmailSender()
        total = len(recipients) if recipients else 0
        results = []

        for idx, recipient in enumerate(recipients or [], start=1):
            self.update_state(
                state='PROGRESS',
                meta={'progress': int(idx / max(total, 1) * 100), 'message': f'Envoi {idx}/{total}'}
            )
            result = sender.send_email(
                to=recipient.get('email'),
                subject=subject_template.format(nom=recipient.get('nom', ''), entreprise=recipient.get('entreprise', '')),
                body=body_template.format(nom=recipient.get('nom', ''), entreprise=recipient.get('entreprise', ''))
            )
            results.append({**recipient, **result})

        return {'success': True, 'results': results, 'total': total}
    except Exception as e:
        logger.error(f'Erreur envoi bulk emails: {e}', exc_info=True)
        raise


@celery.task(bind=True)
def send_campagne_task(self, campagne_id, recipients, template_id=None, subject=None, custom_message=None, delay=2):
    """
    Envoie une campagne email complète avec suivi en temps réel
    
    Args:
        campagne_id: ID de la campagne dans la BDD
        recipients: Liste de dicts {email, nom, entreprise, entreprise_id}
        template_id: ID du template (optionnel)
        subject: Sujet de l'email
        custom_message: Message personnalisé si pas de template
        delay: Délai entre envois (secondes)
    
    Returns:
        dict: Résultats de la campagne
    """
    from services.database import Database
    from services.template_manager import TemplateManager
    from services.email_sender import EmailSender
    import time
    
    db = Database()
    template_manager = TemplateManager()
    email_sender = EmailSender(enable_tracking=True)
    
    # Récupérer l'URL de base depuis la config ou utiliser localhost par défaut
    try:
        from config import BASE_URL
        base_url = BASE_URL if BASE_URL else 'http://localhost:5000'
    except:
        base_url = 'http://localhost:5000'
    
    tracker = EmailTracker(base_url=base_url)
    
    total = len(recipients) if recipients else 0
    results = []
    total_sent = 0
    total_failed = 0
    logs = []  # Liste des logs pour l'affichage en temps réel
    
    logger.info(f'=== Démarrage campagne {campagne_id} ===')
    logger.info(f'Total destinataires: {total}')
    logger.info(f'Template ID: {template_id or "Aucun"}')
    logger.info(f'Sujet: {subject or "Non défini"}')
    logger.info(f'Délai entre envois: {delay}s')
    
    # Mettre à jour le statut de la campagne
    db.update_campagne(campagne_id, statut='running', total_destinataires=total)
    
    # Charger le template si fourni
    template = None
    if template_id:
        logger.info(f'Chargement du template {template_id}...')
        template = template_manager.get_template(template_id)
        if template:
            logger.info(f'Template chargé: {template.get("name", "Sans nom")}')
        else:
            logger.warning(f'Template {template_id} introuvable')
    
    try:
        for idx, recipient in enumerate(recipients or [], start=1):
            recipient_email = recipient.get('email', 'N/A')
            recipient_nom = recipient.get('nom', 'N/A')
            recipient_entreprise = recipient.get('entreprise', 'N/A')
            
            logger.info(f'--- Email {idx}/{total}: {recipient_email} ---')
            logger.debug(f'Destinataire: {recipient_nom} ({recipient_entreprise})')
            # Mettre à jour la progression avec logs
            progress = int((idx / max(total, 1)) * 100)
            log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'info',
                'message': f'Traitement email {idx}/{total}: {recipient_email}'
            }
            logs.append(log_entry)
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': f'Envoi {idx}/{total} : {recipient.get("email", "N/A")}',
                    'current': idx,
                    'total': total,
                    'sent': total_sent,
                    'failed': total_failed,
                    'logs': logs[-20:]  # Garder les 20 derniers logs
                }
            )
            
            # Personnaliser le message
            logger.debug(f'Personnalisation du message pour {recipient_email}...')
            if template_id and template:
                message = template_manager.render_template(
                    template_id,
                    recipient.get('nom', ''),
                    recipient.get('entreprise', ''),
                    recipient.get('email', '')
                )
                email_subject = subject or template.get('subject', 'Prospection')
                logger.debug(f'Message généré depuis template (longueur: {len(message)} caractères)')
            elif custom_message:
                message = custom_message.format(
                    nom=recipient.get('nom', 'Monsieur/Madame'),
                    entreprise=recipient.get('entreprise', 'votre entreprise'),
                    email=recipient.get('email', '')
                )
                email_subject = subject or 'Prospection'
                logger.debug(f'Message personnalisé généré (longueur: {len(message)} caractères)')
            else:
                error_msg = f'Pas de template ni message personnalisé pour {recipient_email}'
                logger.error(error_msg)
                log_entry = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': error_msg
                }
                logs.append(log_entry)
                result = {
                    'email': recipient.get('email'),
                    'success': False,
                    'message': 'Template ou message requis'
                }
                results.append(result)
                total_failed += 1
                db.save_email_envoye(
                    campagne_id=campagne_id,
                    entreprise_id=recipient.get('entreprise_id'),
                    email=recipient.get('email'),
                    nom_destinataire=recipient.get('nom'),
                    sujet=subject or 'Prospection',
                    statut='failed',
                    erreur='Template ou message requis'
                )
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': progress,
                        'message': f'Erreur {idx}/{total} : {recipient_email}',
                        'current': idx,
                        'total': total,
                        'sent': total_sent,
                        'failed': total_failed,
                        'logs': logs[-20:]
                    }
                )
                continue
            
            # Générer un token de tracking unique
            logger.debug(f'Génération du token de tracking...')
            tracking_token = tracker.generate_tracking_token()
            logger.debug(f'Token généré: {tracking_token[:20]}...')
            
            # Convertir le message en HTML si c'est du texte
            html_message = None
            if template_id and template:
                # Le template peut déjà être en HTML
                html_message = message
                logger.debug('Utilisation du template HTML directement')
            elif custom_message:
                # Convertir le texte en HTML
                logger.debug('Conversion du message texte en HTML...')
                html_message = tracker.convert_text_to_html(message)
                logger.debug(f'Message HTML généré (longueur: {len(html_message)} caractères)')
            
            # Envoyer l'email avec tracking
            logger.info(f'Envoi de l\'email à {recipient_email}...')
            log_entry = {
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'info',
                'message': f'Envoi en cours: {recipient_email}'
            }
            logs.append(log_entry)
            
            try:
                result = email_sender.send_email(
                    to=recipient['email'],
                    subject=email_subject,
                    body=message,
                    recipient_name=recipient.get('nom', ''),
                    html_body=html_message,
                    tracking_token=tracking_token
                )
                
                if result['success']:
                    logger.info(f'✓ Email envoyé avec succès à {recipient_email}')
                    log_entry = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'level': 'success',
                        'message': f'✓ Email envoyé: {recipient_email}'
                    }
                else:
                    error_detail = result.get('message', 'Erreur inconnue')
                    logger.warning(f'✗ Échec envoi à {recipient_email}: {error_detail}')
                    log_entry = {
                        'timestamp': time.strftime('%H:%M:%S'),
                        'level': 'error',
                        'message': f'✗ Échec: {recipient_email} - {error_detail}'
                    }
                logs.append(log_entry)
            except Exception as e:
                error_detail = str(e)
                logger.error(f'✗ Exception lors de l\'envoi à {recipient_email}: {error_detail}', exc_info=True)
                log_entry = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'level': 'error',
                    'message': f'✗ Exception: {recipient_email} - {error_detail}'
                }
                logs.append(log_entry)
                result = {
                    'success': False,
                    'message': error_detail
                }
            
            # Sauvegarder le résultat avec le token de tracking (normalisé - entreprise via entreprise_id)
            logger.debug(f'Sauvegarde du résultat en base de données...')
            email_id = db.save_email_envoye(
                campagne_id=campagne_id,
                entreprise_id=recipient.get('entreprise_id'),
                email=recipient['email'],
                nom_destinataire=recipient.get('nom'),
                sujet=email_subject,
                statut='sent' if result['success'] else 'failed',
                erreur=None if result['success'] else result.get('message', 'Erreur inconnue')
            )
            
            # Mettre à jour le token de tracking
            if email_id:
                logger.debug(f'Association du token de tracking (email_id: {email_id})')
                db.update_email_tracking_token(email_id, tracking_token)
            
            if result['success']:
                total_sent += 1
                logger.debug(f'Total envoyés: {total_sent}/{total}')
            else:
                total_failed += 1
                logger.debug(f'Total échecs: {total_failed}/{total}')
            
            results.append({
                **recipient,
                **result
            })
            
            # Mettre à jour la progression avec les nouveaux logs
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': f'Envoi {idx}/{total} : {recipient.get("email", "N/A")}',
                    'current': idx,
                    'total': total,
                    'sent': total_sent,
                    'failed': total_failed,
                    'logs': logs[-20:]
                }
            )
            
            # Délai entre les envois
            if delay > 0 and idx < total:
                logger.debug(f'Attente de {delay}s avant le prochain envoi...')
                time.sleep(delay)
        
        # Mettre à jour le statut final de la campagne
        final_statut = 'completed' if total_failed == 0 else ('completed' if total_sent > 0 else 'failed')
        db.update_campagne(
            campagne_id,
            statut=final_statut,
            total_envoyes=total,
            total_reussis=total_sent
        )
        
        logger.info(f'=== Campagne {campagne_id} terminée ===')
        logger.info(f'Total envoyés: {total_sent}/{total}')
        logger.info(f'Total échecs: {total_failed}/{total}')
        logger.info(f'Statut final: {final_statut}')
        
        log_entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'success' if final_statut == 'completed' else 'warning',
            'message': f'Campagne terminée: {total_sent} envoyés, {total_failed} échecs'
        }
        logs.append(log_entry)
        
        return {
            'success': True,
            'campagne_id': campagne_id,
            'results': results,
            'total': total,
            'total_sent': total_sent,
            'total_failed': total_failed,
            'logs': logs
        }
    
    except Exception as e:
        error_detail = str(e)
        logger.error(f'=== Erreur fatale campagne {campagne_id} ===', exc_info=True)
        logger.error(f'Erreur: {error_detail}')
        
        log_entry = {
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'message': f'Erreur fatale: {error_detail}'
        }
        logs.append(log_entry)
        
        db.update_campagne(campagne_id, statut='failed')
        
        # Émettre un dernier état avec l'erreur
        try:
            self.update_state(
                state='FAILURE',
                meta={
                    'error': error_detail,
                    'logs': logs[-20:]
                }
            )
        except:
            pass
        
        raise
