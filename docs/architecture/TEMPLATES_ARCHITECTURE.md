# Architecture des Templates - Optimisation

## Vue d'ensemble

L'architecture des templates a été optimisée pour améliorer la maintenabilité, la réutilisabilité et les performances.

## Structure avant/après

### Avant
```
templates/
├── base.html
├── dashboard.html
├── entreprises.html
├── analyses_techniques.html
└── ... (tous les templates à la racine)
```

**Problèmes** :
- Pas d'organisation
- Duplication de code HTML
- Pas de réutilisation de composants
- Navigation et scripts dupliqués dans base.html

### Après
```
templates/
├── base.html              # Template de base optimisé
├── components/            # Composants réutilisables (macros)
│   ├── page_header.html
│   ├── filters_section.html
│   ├── modal.html
│   ├── progress_section.html
│   ├── card.html
│   └── stats_grid.html
├── partials/              # Partials réutilisables (includes)
│   ├── head_meta.html
│   ├── navigation.html
│   ├── footer.html
│   ├── flash_messages.html
│   ├── websocket_indicator.html
│   └── base_scripts.html
└── pages/                 # Pages principales
    ├── dashboard.html
    ├── entreprises.html
    └── ...
```

## Composants (Macros Jinja2)

### page_header
En-tête de page standardisé avec titre et description optionnels.

**Utilisation** :
```jinja2
{% from 'components/page_header.html' import page_header %}
{{ page_header('Titre', 'Description') }}
```

### filters_section
Section de filtres réutilisable avec grille et actions.

**Utilisation** :
```jinja2
{% from 'components/filters_section.html' import filters_section %}
{{ filters_section({
    'title': 'Filtres',
    'items': [
        {'id': 'filter-secteur', 'type': 'select', 'label': 'Secteur', 'options': [...]}
    ],
    'actions': [
        {'id': 'btn-apply', 'type': 'primary', 'label': 'Appliquer'}
    ]
}) }}
```

### modal
Modale générique avec header, body et footer optionnels.

**Utilisation** :
```jinja2
{% from 'components/modal.html' import modal %}
{{ modal('my-modal', 'Titre', size='large') }}
```

### progress_section
Barre de progression avec message.

**Utilisation** :
```jinja2
{% from 'components/progress_section.html' import progress_section %}
{{ progress_section('analysis-progress', 'progress-message') }}
```

### card
Carte générique avec header, body et footer.

**Utilisation** :
```jinja2
{% from 'components/card.html' import card %}
{{ card(header='<h2>Titre</h2>', body='<p>Contenu</p>') }}
```

### stats_grid
Grille de statistiques standardisée.

**Utilisation** :
```jinja2
{% from 'components/stats_grid.html' import stats_grid %}
{{ stats_grid([
    {'id': 'stat-1', 'label': 'Label 1'},
    {'id': 'stat-2', 'label': 'Label 2'}
]) }}
```

## Partials (Includes)

### head_meta.html
Meta tags, favicons et viewport. Centralisé pour faciliter les mises à jour.

### navigation.html
Navigation principale avec menus déroulants. Facilite l'ajout/modification de liens.

### footer.html
Pied de page standardisé.

### flash_messages.html
Affichage des messages flash Flask. Réutilisable partout.

### websocket_indicator.html
Indicateur de statut WebSocket avec script associé.

### base_scripts.html
Scripts JavaScript de base (Socket.IO, main.js, websocket.js). Chargement optimisé.

## Optimisation des dépendances

### CSS
- **style.css** : Chargé une seule fois dans `base.html`
- **extra_css** : Bloc pour CSS spécifiques à une page

### JavaScript
- **Socket.IO** : Chargé une seule fois dans `base_scripts.html`
- **main.js** : Chargé une seule fois dans `base_scripts.html`
- **websocket.js** : Chargé une seule fois dans `base_scripts.html`
- **extra_js** : Bloc pour scripts spécifiques (Chart.js, Leaflet, etc.)

### Chargement conditionnel
Les bibliothèques externes sont chargées uniquement dans les pages qui en ont besoin :

```jinja2
{% block extra_js %}
{# Chart.js uniquement pour le dashboard #}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="{{ url_for('static', filename='js/dashboard.js') }}" defer></script>
{% endblock %}
```

## Bénéfices

### Maintenabilité
- **Code centralisé** : Modifications dans un seul endroit
- **Réutilisabilité** : Composants partagés entre pages
- **Organisation** : Structure claire et logique

### Performance
- **Moins de duplication** : Code HTML réduit
- **Chargement optimisé** : Scripts chargés uniquement où nécessaire
- **Cache navigateur** : Composants partagés mis en cache

### Développement
- **Rapidité** : Création de nouvelles pages plus rapide
- **Cohérence** : Interface utilisateur uniforme
- **Documentation** : Structure auto-documentée

## Migration

### Étape 1 : Structure créée
✓ Dossiers `components/`, `partials/`, `pages/` créés
✓ Composants et partials extraits
✓ `base.html` optimisé

### Étape 2 : Templates migrés
✓ 21 templates copiés vers `pages/`
✓ Anciens templates conservés pour compatibilité

### Étape 3 : Routes mises à jour (en cours)
- Routes mises à jour progressivement pour utiliser `pages/...`
- Fallback sur anciens templates si `pages/` non disponible

### Étape 4 : Refactorisation progressive
- Remplacer les patterns répétitifs par des composants
- Utiliser les partials pour les parties communes
- Optimiser le chargement des dépendances

## Exemple complet

### Avant
```jinja2
{% extends "base.html" %}
{% block content %}
<div class="page-header">
    <h1>Dashboard</h1>
    <p>Description</p>
</div>
<div class="stats-grid">
    <div class="stat-card">...</div>
    <!-- Répété 4 fois -->
</div>
{% endblock %}
```

### Après
```jinja2
{% extends "base.html" %}
{% from 'components/page_header.html' import page_header %}
{% from 'components/stats_grid.html' import stats_grid %}

{% block content %}
{{ page_header('Dashboard', 'Description') }}
{{ stats_grid([...]) }}
{% endblock %}
```

**Gain** : Code réduit de ~60%, plus maintenable, plus lisible.

## Prochaines étapes

1. ✅ Structure créée
2. ✅ Composants de base créés
3. ✅ Partials extraits
4. ✅ Templates migrés vers `pages/`
5. ⏳ Mise à jour progressive des routes
6. ⏳ Refactorisation des templates pour utiliser les composants
7. ⏳ Optimisation finale des dépendances JS/CSS

## Notes

- Les anciens templates fonctionnent toujours (compatibilité)
- La migration est progressive et non-bloquante
- Les composants peuvent être étendus selon les besoins
- La documentation est dans `templates/README.md`

