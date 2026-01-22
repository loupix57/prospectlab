"""
Utilitaire pour formater les noms depuis différents formats (JSON, string, etc.)
"""

import json


def format_name(name_data):
    """
    Formate un nom depuis différents formats possibles.
    
    Args:
        name_data: Peut être :
            - Une chaîne JSON (ex: '{"first_name": "John", "last_name": "Doe"}')
            - Un dictionnaire Python
            - Une chaîne simple (ex: "John Doe")
            - None
    
    Returns:
        str: Nom formaté (ex: "John Doe") ou "N/A" si aucun nom valide
    """
    if not name_data:
        return 'N/A'
    
    # Si c'est déjà une chaîne simple, la retourner telle quelle
    if isinstance(name_data, str):
        # Essayer de parser si c'est du JSON
        if name_data.strip().startswith('{') or name_data.strip().startswith('['):
            try:
                parsed = json.loads(name_data)
                if isinstance(parsed, dict):
                    return _format_from_dict(parsed)
                # Si c'est une liste, prendre le premier élément
                if isinstance(parsed, list) and len(parsed) > 0:
                    if isinstance(parsed[0], dict):
                        return _format_from_dict(parsed[0])
                    return str(parsed[0])
            except (json.JSONDecodeError, ValueError):
                # Si le parsing échoue, c'est probablement une chaîne simple
                pass
        
        # Si c'est une chaîne simple, la retourner
        return name_data.strip() if name_data.strip() else 'N/A'
    
    # Si c'est un dictionnaire
    if isinstance(name_data, dict):
        return _format_from_dict(name_data)
    
    # Sinon, convertir en chaîne
    return str(name_data) if name_data else 'N/A'


def _format_from_dict(name_dict):
    """
    Formate un nom depuis un dictionnaire.
    
    Args:
        name_dict: Dictionnaire avec first_name, last_name, full_name, etc.
    
    Returns:
        str: Nom formaté
    """
    if not name_dict:
        return 'N/A'
    
    # Essayer full_name d'abord
    full_name = name_dict.get('full_name') or name_dict.get('fullname')
    if full_name:
        return str(full_name).strip()
    
    # Sinon, construire depuis first_name et last_name
    first_name = name_dict.get('first_name') or name_dict.get('firstname') or ''
    last_name = name_dict.get('last_name') or name_dict.get('lastname') or ''
    
    # Nettoyer les valeurs
    first_name = str(first_name).strip() if first_name else ''
    last_name = str(last_name).strip() if last_name else ''
    
    # Construire le nom complet
    if first_name and last_name:
        return f'{first_name} {last_name}'
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    
    # Si rien n'est disponible, essayer 'name' comme fallback
    name = name_dict.get('name')
    if name:
        return str(name).strip()
    
    return 'N/A'

