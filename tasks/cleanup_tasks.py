"""
Tâches Celery pour le nettoyage automatique des fichiers
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from celery import Task
from celery_app import celery
from config import UPLOAD_FOLDER, EXPORT_FOLDER
from services.logging_config import setup_logger

# Créer un logger spécifique pour les tâches de cleanup
logger = setup_logger('tasks.cleanup_tasks', 'cleanup_tasks.log', console=True)


@celery.task(bind=True, name='cleanup.cleanup_old_files')
def cleanup_old_files_task(self, max_age_hours=6):
    """
    Nettoie les fichiers uploads et exports plus anciens que max_age_hours heures.
    
    Args:
        self: Instance de la tâche Celery
        max_age_hours (int): Nombre d'heures après lesquelles les fichiers sont supprimés (défaut: 6)
        
    Returns:
        dict: Statistiques du nettoyage (fichiers supprimés, espace libéré)
        
    Example:
        >>> cleanup_old_files_task.delay(max_age_hours=6)
    """
    try:
        logger.info(f'[Cleanup] Démarrage du nettoyage automatique (fichiers de plus de {max_age_hours}h)')
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Démarrage du nettoyage...'}
        )
        
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        deleted_files = []
        total_size_freed = 0
        
        # Convertir les Path en string pour os.path.exists() et os.walk()
        upload_folder_str = str(UPLOAD_FOLDER)
        export_folder_str = str(EXPORT_FOLDER)
        
        folders_to_clean = [
            ('uploads', upload_folder_str),
            ('exports', export_folder_str)
        ]
        
        logger.info(f'[Cleanup] Analyse des dossiers: {[f[0] for f in folders_to_clean]}')
        logger.info(f'[Cleanup] Chemin uploads: {upload_folder_str}')
        logger.info(f'[Cleanup] Chemin exports: {export_folder_str}')
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'message': f'Analyse des dossiers (max {max_age_hours}h)...'}
        )
        
        for folder_name, folder_path in folders_to_clean:
            folder_path_str = str(folder_path)
            if not os.path.exists(folder_path_str):
                logger.warning(f'[Cleanup] Dossier {folder_name} introuvable: {folder_path_str}')
                continue
            
            logger.info(f'[Cleanup] Nettoyage du dossier {folder_name}: {folder_path_str}')
            
            folder_deleted_count = 0
            folder_size_freed = 0
            
            try:
                for root, dirs, files in os.walk(folder_path_str):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        
                        try:
                            # Vérifier l'âge du fichier
                            file_mtime = os.path.getmtime(filepath)
                            file_age = current_time - file_mtime
                            
                            if file_age > max_age_seconds:
                                file_size = os.path.getsize(filepath)
                                os.remove(filepath)
                                deleted_files.append({
                                    'path': filepath,
                                    'size': file_size,
                                    'age_hours': file_age / 3600
                                })
                                total_size_freed += file_size
                                folder_deleted_count += 1
                                folder_size_freed += file_size
                                logger.debug(f'[Cleanup] Fichier supprimé: {os.path.basename(filepath)} (âge: {file_age/3600:.2f}h, taille: {file_size} octets)')
                        except OSError as e:
                            logger.warning(f'[Cleanup] Impossible de supprimer {filepath}: {e}')
                            continue
                    
                    # Nettoyer les dossiers vides
                    for dirname in dirs:
                        dirpath = os.path.join(root, dirname)
                        try:
                            if not os.listdir(dirpath):  # Dossier vide
                                os.rmdir(dirpath)
                                logger.debug(f'[Cleanup] Dossier vide supprimé: {dirpath}')
                        except OSError:
                            pass  # Ignorer les erreurs de suppression de dossiers
                
                if folder_deleted_count > 0:
                    logger.info(f'[Cleanup] Dossier {folder_name}: {folder_deleted_count} fichiers supprimés, {round(folder_size_freed / (1024 * 1024), 2)} MB libérés')
                else:
                    logger.info(f'[Cleanup] Dossier {folder_name}: aucun fichier à supprimer')
                            
            except Exception as e:
                logger.error(f'[Cleanup] Erreur lors du nettoyage du dossier {folder_name}: {e}', exc_info=True)
        
        result = {
            'success': True,
            'deleted_count': len(deleted_files),
            'total_size_freed': total_size_freed,
            'size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
            'deleted_files': deleted_files[:50],  # Limiter à 50 fichiers pour éviter des réponses trop lourdes
            'max_age_hours': max_age_hours
        }
        
        logger.info(
            f'[Cleanup] Nettoyage terminé: {len(deleted_files)} fichiers supprimés, '
            f'{result["size_freed_mb"]} MB libérés'
        )
        
        # Log détaillé pour le beat
        if deleted_files:
            logger.info(f'[Cleanup] Exemples de fichiers supprimés: {", ".join([os.path.basename(f["path"]) for f in deleted_files[:5]])}')
        
        return result
        
    except Exception as e:
        logger.error(f'Erreur lors du nettoyage: {e}', exc_info=True)
        raise

