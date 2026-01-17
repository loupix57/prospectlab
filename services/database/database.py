"""
Classe Database principale qui combine tous les mixins
"""

from .base import DatabaseBase
from .entreprises import EntreprisesMixin
from .analyses import AnalysesMixin
from .scrapers import ScrapersMixin
from .campagnes import CampagnesMixin


class Database(DatabaseBase, EntreprisesMixin, AnalysesMixin, ScrapersMixin, CampagnesMixin):
    """
    Classe Database principale qui hérite de DatabaseBase et combine tous les mixins
    
    Cette classe fournit toutes les méthodes de gestion de la base de données
    via l'héritage multiple (mixins) pour une meilleure organisation du code.
    """
    pass

