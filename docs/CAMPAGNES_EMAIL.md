# Système de Campagnes Email avec Tracking

## Vue d'ensemble

Le système de campagnes email permet d'envoyer des emails en masse à des prospects avec un suivi complet des performances : ouvertures, clics, temps de lecture, etc.

## Fonctionnalités principales

### 1. Création de campagnes

- Sélection de destinataires depuis la base d'entreprises
- Choix de template ou message personnalisé
- Configuration du sujet et du message
- Délai configurable entre les envois

### 2. Tracking des emails

#### Pixel de tracking invisible
- Pixel 1x1 transparent injecté dans chaque email
- Détection automatique des ouvertures
- Enregistrement de l'IP et du User-Agent

#### Tracking des clics
- Tokenisation de tous les liens dans l'email
- Redirection via `/track/click/<token>`
- Enregistrement de l'URL cliquée, IP et User-Agent

#### Statistiques collectées
- Nombre d'ouvertures par email
- Nombre de clics par email
- Temps de lecture moyen
- Taux d'ouverture global
- Taux de clic global

### 3. Interface de résultats

#### Modale de statistiques
- Vue d'ensemble avec 4 cartes principales :
  - Emails envoyés
  - Ouvertures (total + pourcentage)
  - Clics (total + pourcentage)
  - Taux d'ouverture
- Indicateurs de performance :
  - Taux de clic
  - Temps de lecture moyen
- Tableau détaillé par contact :
  - Nom et email du contact
  - Entreprise
  - Statut (Envoyé, Ouvert, Clic, Échec)
  - Nombre d'ouvertures
  - Nombre de clics
  - Date d'envoi
  - Dernière ouverture

### 4. Suivi en temps réel

- WebSocket pour les mises à jour en direct
- Barre de progression pendant l'envoi
- Notifications de succès/erreur
- Mise à jour automatique des statistiques

## Architecture technique

### Backend

#### Base de données
- Table `campagnes_email` : informations des campagnes
- Table `emails_envoyes` : emails envoyés avec token de tracking
- Table `email_tracking_events` : événements de tracking (open, click, etc.)
- Index optimisés pour les performances de lecture/écriture
- Contraintes `ON DELETE CASCADE` pour l'intégrité référentielle

#### Services

**EmailTracker** (`services/email_tracker.py`)
- Génération de tokens uniques
- Injection du pixel de tracking
- Tokenisation des liens

**EmailSender** (`services/email_sender.py`)
- Envoi d'emails avec tracking activé
- Gestion des erreurs

**Database** (`services/database/`)
- Architecture modulaire avec mixins
- `campagnes.py` : gestion des campagnes et tracking
- Méthodes optimisées avec `LEFT JOIN` pour les statistiques

#### Routes API

- `POST /api/campagnes` : Créer une campagne
- `GET /api/campagnes` : Lister les campagnes
- `GET /api/campagnes/<id>` : Détails d'une campagne
- `DELETE /api/campagnes/<id>` : Supprimer une campagne
- `GET /api/tracking/campagne/<id>` : Statistiques de tracking
- `GET /track/pixel/<token>` : Pixel de tracking
- `GET /track/click/<token>` : Redirection trackée

#### Tâches Celery

**send_campagne_task** (`tasks/email_tasks.py`)
- Envoi asynchrone des emails
- Mise à jour de la progression en temps réel
- Logs détaillés pour le débogage
- Gestion des erreurs par email

### Frontend

#### Structure

**JavaScript** (`static/js/campagnes.js`)
- Gestion de l'interface utilisateur
- Communication WebSocket pour le temps réel
- Affichage des statistiques dans une modale moderne

**CSS** (`static/css/campagnes.css`)
- Styles séparés pour une meilleure organisation
- Design moderne et responsive
- Animations et transitions

**HTML** (`templates/campagnes.html`)
- Interface de gestion des campagnes
- Modale de création
- Modale de résultats

#### WebSocket

Événements écoutés :
- `campagne_progress` : Mise à jour de progression
- `campagne_complete` : Campagne terminée
- `campagne_error` : Erreur lors de l'envoi

## Utilisation

### Créer une campagne

1. Cliquer sur "Nouvelle campagne"
2. Remplir le formulaire :
   - Nom de la campagne
   - Sujet de l'email
   - Template ou message personnalisé
   - Sélectionner les destinataires
3. Cliquer sur "Créer et envoyer"
4. La campagne démarre automatiquement

### Consulter les résultats

1. Cliquer sur "Voir détails" sur une campagne
2. La modale affiche :
   - Statistiques globales
   - Indicateurs de performance
   - Détails par contact

### Suivi en temps réel

- Pendant l'envoi, la barre de progression se met à jour automatiquement
- Les statistiques sont mises à jour en temps réel
- Notifications en cas de succès ou d'erreur

## Optimisations

### Base de données

- Index sur les colonnes fréquemment interrogées
- `ON DELETE CASCADE` pour éviter les orphelins
- `LEFT JOIN` pour optimiser les requêtes de statistiques
- Contraintes `CHECK` pour valider les données

### Performance

- Envoi asynchrone avec Celery
- Délai configurable entre les envois
- Mise à jour progressive de l'interface
- Requêtes optimisées avec index

## Sécurité

- Tokens uniques générés avec `secrets.token_urlsafe()`
- Validation des données côté serveur
- Protection contre les injections SQL (paramètres liés)
- Headers de cache pour le pixel de tracking

## Maintenance

### Logs

- Logs détaillés dans `tasks/email_tasks.py`
- Logs de tracking dans la base de données
- Erreurs affichées dans l'interface

### Nettoyage

- Les logs de debug sont minimisés côté frontend
- Seules les erreurs critiques sont loggées
- Les logs backend sont conservés pour le débogage

