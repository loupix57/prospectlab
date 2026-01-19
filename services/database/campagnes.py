"""
Module de gestion des campagnes email
Contient toutes les méthodes liées aux campagnes email
"""

import json
from .base import DatabaseBase


class CampagneManager(DatabaseBase):
    """
    Gère toutes les opérations sur les campagnes email
    """
    
    def __init__(self, *args, **kwargs):
        """Initialise le module campagnes"""
        super().__init__(*args, **kwargs)
    
    # Note: Les méthodes de campagnes email n'ont pas encore été implémentées dans database.py
    # Ce module est prêt pour les futures implémentations
