"""
Module de base pour la gestion de la base de données
Contient la classe Database de base avec la connexion et les méthodes communes
"""

import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseBase:
    """
    Classe de base pour la gestion de la base de données
    Gère la connexion et l'initialisation
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialise la connexion à la base de données
        
        Args:
            db_path: Chemin vers le fichier de base de données (optionnel)
        """
        if db_path is None:
            # Vérifier si un chemin est défini dans les variables d'environnement
            import os
            env_db_path = os.environ.get('DATABASE_PATH')
            if env_db_path:
                db_path = env_db_path
            else:
                app_dir = Path(__file__).parent.parent.parent
                db_path = app_dir / 'prospectlab.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtient une connexion à la base de données
        
        Returns:
            Connexion SQLite avec row_factory configuré
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Activer les foreign keys pour que CASCADE fonctionne
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

