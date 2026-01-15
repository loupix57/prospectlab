"""
Script wrapper pour démarrer Celery avec une meilleure gestion de Ctrl+C sur Windows

Usage:
    python run_celery.py
"""

import signal
import sys
import os
import threading
import time
import subprocess
import socket
import uuid

def signal_handler(sig, frame):
    """Gère Ctrl+C proprement"""
    print('\n\n[!] Arrêt de Celery demandé...')
    # Arrêter les processus Celery si ils existent
    global celery_process, beat_process
    if beat_process and beat_process.poll() is None:
        beat_process.terminate()
        try:
            beat_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            beat_process.kill()
    if celery_process and celery_process.poll() is None:
        celery_process.terminate()
        try:
            celery_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            celery_process.kill()
    # Arrêt forcé immédiat sur Windows
    os._exit(0)

# Variables globales pour les processus Celery
celery_process = None
beat_process = None

def run_celery_worker():
    """Lance le worker Celery via subprocess"""
    global celery_process
    try:
        # Générer un nom unique pour ce worker (hostname + UUID court)
        hostname = socket.gethostname()
        worker_id = str(uuid.uuid4())[:8]
        worker_name = f"{hostname}-{worker_id}"
        
        # Sur Windows, --beat ne fonctionne pas, donc on lance juste le worker
        # Le beat sera lancé dans un processus séparé
        celery_process = subprocess.Popen(
            [sys.executable, '-m', 'celery', '-A', 'celery_app', 'worker',
             '--loglevel=info', '--pool=solo', f'--hostname={worker_name}'],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        celery_process.wait()
    except KeyboardInterrupt:
        print('\n\n[!] Arrêt de Celery worker...')
        if celery_process:
            celery_process.terminate()
        os._exit(0)
    except Exception as e:
        print(f'Erreur lors du lancement de Celery worker: {e}')
        import traceback
        traceback.print_exc()
        if celery_process:
            celery_process.terminate()
        os._exit(1)

def run_celery_beat():
    """Lance le beat scheduler Celery via subprocess (nécessaire sur Windows)"""
    global beat_process
    try:
        # Lancer le beat scheduler dans un processus séparé
        beat_process = subprocess.Popen(
            [sys.executable, '-m', 'celery', '-A', 'celery_app', 'beat',
             '--loglevel=info'],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        beat_process.wait()
    except KeyboardInterrupt:
        print('\n\n[!] Arrêt de Celery beat...')
        if beat_process:
            beat_process.terminate()
        os._exit(0)
    except Exception as e:
        print(f'Erreur lors du lancement de Celery beat: {e}')
        import traceback
        traceback.print_exc()
        if beat_process:
            beat_process.terminate()
        os._exit(1)

def main():
    """Point d'entrée principal"""
    # Variable globale pour contrôler l'arrêt
    shutdown_event = threading.Event()
    
    # Enregistrer le gestionnaire de signal AVANT de lancer Celery
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == 'win32':
        signal.signal(signal.SIGTERM, signal_handler)
    
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    print('Démarrage du worker Celery avec Beat (tâches périodiques)...')
    print('  - Worker: exécute les tâches asynchrones')
    print('  - Beat: exécute les tâches périodiques (nettoyage toutes les heures)')
    print('  - Note: Sur Windows, worker et beat sont lancés dans des processus séparés')
    print('Appuyez sur Ctrl+C pour arrêter Celery\n')
    
    # Sur Windows, lancer worker et beat dans des threads séparés
    # car --beat ne fonctionne pas avec le worker sur Windows
    celery_thread = threading.Thread(target=run_celery_worker, daemon=False)
    beat_thread = threading.Thread(target=run_celery_beat, daemon=False)
    
    # Démarrer les deux threads
    celery_thread.start()
    time.sleep(1)  # Attendre un peu avant de démarrer le beat
    beat_thread.start()
    
    # Attendre que les threads démarrent
    time.sleep(0.5)
    
    # Surveiller l'arrêt dans le thread principal
    try:
        # Sur Windows, surveiller l'entrée standard dans le thread principal
        if sys.platform == 'win32':
            try:
                import msvcrt
                while (celery_thread.is_alive() or beat_thread.is_alive()) and not shutdown_event.is_set():
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\x03':  # Ctrl+C
                            print('\n\n[!] Ctrl+C détecté - Arrêt de Celery...')
                            os._exit(0)
                    time.sleep(0.1)
            except ImportError:
                # msvcrt non disponible, attendre simplement
                celery_thread.join()
                beat_thread.join()
        else:
            # Sur Linux/Mac, attendre normalement
            celery_thread.join()
            beat_thread.join()
    except KeyboardInterrupt:
        print('\n\n[!] Arrêt de Celery...')
        os._exit(0)

if __name__ == '__main__':
    main()

