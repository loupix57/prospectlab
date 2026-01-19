"""
Tâches Celery pour les analyses techniques et Pentest

Ces tâches permettent d'exécuter les analyses techniques de manière asynchrone,
avec sauvegarde automatique dans la base de données.
"""

from celery_app import celery
from services.technical_analyzer import TechnicalAnalyzer
from services.pentest_analyzer import PentestAnalyzer
from services.database import Database
from services.logging_config import setup_logger
import logging
import json

# Configurer le logger pour cette tâche (niveau INFO pour limiter le bruit)
logger = setup_logger(__name__, 'technical_analysis_tasks.log', level=logging.INFO)


@celery.task(bind=True)
def technical_analysis_task(self, url, entreprise_id=None, enable_nmap=False):
    """
    Tâche Celery pour effectuer une analyse technique complète d'un site web
    
    Args:
        self: Instance de la tâche Celery (bind=True)
        url (str): URL du site à analyser
        entreprise_id (int, optional): ID de l'entreprise associée
        enable_nmap (bool, optional): Activer le scan Nmap (plus long)
        
    Returns:
        dict: Résultats de l'analyse technique avec analysis_id
        
    Example:
        >>> result = technical_analysis_task.delay('https://example.com', entreprise_id=1)
    """
    try:
        logger.info(f'Demarrage de l analyse technique pour {url} (entreprise_id={entreprise_id}, enable_nmap={enable_nmap})')
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': 'Initialisation de l\'analyse technique...'}
        )
        
        analyzer = TechnicalAnalyzer()
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 30, 'message': 'Analyse en cours...'}
        )
        
        # Analyse technique complète (réduire à 5 pages pour accélérer, max_depth=1)
        results = analyzer.analyze_site_overview(url, max_pages=5, max_depth=1, enable_nmap=enable_nmap)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'message': 'Sauvegarde des résultats...'}
        )
        
        # Sauvegarder dans la base de données (même sans entreprise_id)
        database = Database()
        analysis_id = None
        
        try:
            analysis_id = database.save_technical_analysis(entreprise_id, url, results)
            if entreprise_id:
                logger.info(f'Analyse technique sauvegardee (id={analysis_id}) pour {url} (entreprise_id={entreprise_id})')
            else:
                logger.info(f'Analyse technique sauvegardee (id={analysis_id}) pour {url} (sans entreprise)')
        except Exception as e:
            logger.error(f'Erreur lors de la sauvegarde de l analyse technique pour {url}: {str(e)}', exc_info=True)
            raise
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'Analyse technique terminée!'}
        )
        
        return {
            'success': True,
            'url': url,
            'entreprise_id': entreprise_id,
            'analysis_id': analysis_id,
            'results': results
        }
        
    except Exception as e:
        logger.error(f'Erreur lors de l analyse technique de {url}: {e}', exc_info=True)
        raise


@celery.task(bind=True)
def pentest_analysis_task(self, url, entreprise_id=None, options=None):
    """
    Tâche Celery pour effectuer une analyse Pentest d'un site web
    
    Args:
        self: Instance de la tâche Celery (bind=True)
        url (str): URL du site à analyser
        entreprise_id (int, optional): ID de l'entreprise associée
        options (dict, optional): Options pour l'analyse (scan_sql, scan_xss, etc.)
        
    Returns:
        dict: Résultats de l'analyse Pentest avec analysis_id
        
    Example:
        >>> result = pentest_analysis_task.delay('https://example.com', entreprise_id=1, options={'scan_sql': True})
    """
    try:
        logger.info(f'Démarrage de l\'analyse Pentest pour {url}')
        
        database = Database()
        
        # Vérifier si une analyse existe déjà
        existing = database.get_pentest_analysis_by_url(url)
        if existing:
            # Si une analyse existe et qu'on a un entreprise_id, mettre à jour le lien
            if entreprise_id and existing.get('entreprise_id') != entreprise_id:
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE analyses_pentest SET entreprise_id = ? WHERE id = ?', (entreprise_id, existing['id']))
                conn.commit()
                conn.close()
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 5, 'message': 'Initialisation de l\'analyse de sécurité...'}
        )
        
        analyzer = PentestAnalyzer()
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'message': 'Scan de vulnérabilités en cours...'}
        )
        
        # Lancer l'analyse Pentest
        if options is None:
            options = {}
        pentest_data = analyzer.analyze_pentest(url, options)
        
        if pentest_data.get('error'):
            raise Exception(pentest_data['error'])
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 90, 'message': 'Sauvegarde des résultats...'}
        )
        
        # Sauvegarder ou mettre à jour dans la base de données
        if existing:
            analysis_id = database.update_pentest_analysis(existing['id'], pentest_data)
        else:
            analysis_id = database.save_pentest_analysis(entreprise_id, url, pentest_data)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'Analyse de sécurité terminée!'}
        )
        
        logger.info(f'Analyse Pentest terminée pour {url} (analysis_id: {analysis_id})')
        
        return {
            'success': True,
            'url': url,
            'entreprise_id': entreprise_id,
            'analysis_id': analysis_id,
            'summary': pentest_data.get('summary', {}),
            'risk_score': pentest_data.get('risk_score', 0),
            'updated': existing is not None
        }
        
    except Exception as e:
        logger.error(f'Erreur lors de l analyse Pentest de {url}: {e}', exc_info=True)
        raise


@celery.task(bind=True)
def advanced_technical_analysis_task(self, url):
    """
    Analyse technique avancée (SSL, robots.txt, services tiers).
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 5, 'message': 'Analyse SSL...'})
        parsed = url if url.startswith(('http://', 'https://')) else f'https://{url}'
        domain = parsed.split('//', 1)[1].split('/')[0]
        ssl_info = analyze_ssl_certificate(domain)

        self.update_state(state='PROGRESS', meta={'progress': 40, 'message': 'Analyse robots.txt...'})
        robots_info = analyze_robots_txt(parsed)

        self.update_state(state='PROGRESS', meta={'progress': 70, 'message': 'Analyse services tiers...'})
        services_info = {}
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(parsed, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                services_info = detect_third_party_services(soup, resp.text)
        except Exception as e:
            services_info = {'error': str(e)}

        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': 'Analyse avancée terminée'})

        return {
            'success': True,
            'url': url,
            'ssl': ssl_info,
            'robots': robots_info,
            'services': services_info
        }
    except Exception as e:
        logger.error(f'Erreur analyse technique avancée {url}: {e}', exc_info=True)
        raise

