# Analyse des emails pendant le scraping

## Vue d'ensemble

Cette documentation décrit les améliorations apportées au système de scraping pour intégrer l'analyse automatique des emails trouvés, ainsi que les corrections et optimisations associées.

## Fonctionnalités implémentées

### 1. Analyse automatique des emails pendant le scraping

Lors du scraping d'un site web, les emails trouvés sont maintenant automatiquement analysés avant de passer à l'entreprise suivante.

#### Flux de traitement

1. **Extraction des emails** : Le scraper trouve des emails sur les pages du site
2. **Analyse immédiate** : Chaque email est analysé directement via `EmailAnalyzer` (sans passer par une tâche Celery)
3. **Sauvegarde enrichie** : Les résultats de l'analyse sont sauvegardés avec l'email dans la base de données
4. **Attente de complétion** : Le système attend que toutes les analyses d'emails soient terminées avant de passer à l'entreprise suivante

#### Données d'analyse stockées

Pour chaque email analysé, les informations suivantes sont sauvegardées :

- **provider** : Fournisseur d'email (Gmail, Outlook, etc.)
- **type** : Type d'email (Professionnel, Personnel, Générique)
- **format_valid** : Validité du format de l'email
- **mx_valid** : Validité des enregistrements MX du domaine
- **risk_score** : Score de risque (0-100)
- **domain** : Domaine de l'email
- **name_info** : Informations extraites du nom (prénom, nom, etc.)
- **analyzed_at** : Date et heure de l'analyse

#### Code concerné

- `tasks/scraping_tasks.py` : Modification de `scrape_analysis_task` pour analyser les emails directement
- `services/email_analyzer.py` : Service d'analyse des emails
- `services/database.py` : Sauvegarde des données d'analyse dans `scraper_emails`

### 2. Stockage du page_url pour les emails

Chaque email trouvé est maintenant associé à l'URL de la page où il a été découvert.

#### Modifications apportées

**Avant** : Les emails étaient stockés comme un simple `Set[str]`, perdant l'information de la page source.

**Après** : Les emails sont stockés comme un `Dict[str, str]` (email -> page_url) dans `UnifiedScraper`.

#### Code modifié

- `services/unified_scraper.py` :
  - `self.emails` : Changé de `Set[str]` à `Dict[str, str]`
  - `scrape_page()` : Stocke chaque email avec sa `page_url`
  - `scrape()` : Retourne les emails comme une liste de dictionnaires avec `email` et `page_url`

#### Exemple de structure retournée

```python
{
    'emails': [
        {
            'email': 'contact@example.com',
            'page_url': 'https://example.com/contact'
        },
        ...
    ]
}
```

### 3. Correction du bug d'affichage [object Object]

#### Problème

Dans le modal d'affichage des résultats de scraping, les emails étaient affichés comme "[object Object]" au lieu de l'adresse email.

#### Solution

Modification de la fonction `addEmailToModal` dans `static/js/entreprises.js` pour :

- Extraire la string email si c'est un objet
- Récupérer l'analyse depuis l'objet si disponible
- Afficher correctement l'email et ses badges d'analyse

#### Code modifié

```javascript
function addEmailToModal(email, analysis) {
    // Extraire l'email string si c'est un objet
    let emailStr = email;
    if (typeof email === 'object' && email !== null) {
        emailStr = email.email || email.value || String(email);
        // Si analysis n'est pas fourni mais que l'objet email contient analysis
        if (!analysis && email.analysis) {
            analysis = email.analysis;
        }
    }
    // ... reste du code
}
```

### 4. Renommage des colonnes de la base de données

#### Problème

Les colonnes de la table `scraper_emails` avaient le préfixe `email_` (ex: `email_provider`, `email_type`), ce qui était redondant.

#### Solution

Renommage des colonnes pour enlever le préfixe :

- `email_provider` → `provider`
- `email_type` → `type`
- `email_format_valid` → `format_valid`
- `email_mx_valid` → `mx_valid`
- `email_risk_score` → `risk_score`
- `email_domain` → `domain`
- `email_name_info` → `name_info`
- `email_analyzed_at` → `analyzed_at`

#### Migration automatique

Une migration automatique a été ajoutée dans `services/database.py` :

1. Création des nouvelles colonnes si elles n'existent pas
2. Copie des données des anciennes colonnes vers les nouvelles
3. Les anciennes colonnes restent pour compatibilité (peuvent être supprimées manuellement plus tard)

#### Code modifié

- `services/database.py` :
  - `init_database()` : Ajout de la migration
  - `_save_scraper_emails_in_transaction()` : Utilisation des nouvelles colonnes
  - `get_scraper_emails()` : Lecture depuis les nouvelles colonnes

### 5. Nettoyage des logs de technical_analysis_tasks

#### Problème

Les logs de la tâche d'analyse technique étaient très verbeux (environ 20 logs INFO par analyse), rendant les fichiers de logs difficiles à lire.

#### Solution

Réduction drastique des logs INFO :

- **Avant** : ~20 logs INFO par analyse
- **Après** : 2-3 logs INFO par analyse (démarrage, sauvegarde réussie, erreurs)

Les logs d'erreur et d'avertissement sont conservés pour le débogage.

#### Code modifié

- `tasks/technical_analysis_tasks.py` : Simplification de `technical_analysis_task()`

## Structure de la base de données

### Table scraper_emails

```sql
CREATE TABLE scraper_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraper_id INTEGER NOT NULL,
    entreprise_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    page_url TEXT,
    date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Colonnes d'analyse (sans préfixe email_)
    provider TEXT,
    type TEXT,
    format_valid INTEGER,
    mx_valid INTEGER,
    risk_score INTEGER,
    domain TEXT,
    name_info TEXT,
    analyzed_at TIMESTAMP,
    FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
    FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
    UNIQUE(scraper_id, email)
)
```

## Affichage des résultats

### Dans la fiche entreprise

Les emails scrapés sont affichés avec leurs badges d'analyse :

- Badge **Type** : Professionnel, Personnel, Générique
- Badge **Provider** : Gmail, Outlook, etc.
- Badge **Format** : Format OK / Format invalide
- Badge **MX** : MX OK / MX invalide
- Badge **Risque** : Score de risque (0-100)
- Badge **Nom** : Nom extrait de l'email (si disponible)

### Dans le modal de résultats

Les emails sont affichés avec leur type et leur fournisseur dans le modal de résultats de scraping.

## Logs

### Scraping

Les logs de scraping incluent maintenant des informations sur l'analyse des emails :

```
[Scraping Analyse 1] 3 email(s) trouvé(s) pour Entreprise X, lancement de l'analyse...
[Scraping Analyse 1] Analyse email 1/3: contact@example.com
[Scraping Analyse 1] Analyse email 2/3: info@example.com
[Scraping Analyse 1] Analyse email 3/3: sales@example.com
[Scraping Analyse 1] Tous les emails analysés avec succès pour Entreprise X
```

### Analyse technique

Les logs d'analyse technique ont été simplifiés pour être plus concis :

```
[Technical Analysis] Démarrage pour https://example.com (entreprise_id=1)
[Technical Analysis] Analyse sauvegardée (id=1) pour https://example.com
```

## Impact sur les performances

### Avant

- Les emails étaient analysés après le scraping complet
- Pas de `page_url` stocké
- Logs très verbeux

### Après

- Les emails sont analysés immédiatement pendant le scraping
- Chaque email a son `page_url` associé
- Logs plus concis et lisibles
- Le système attend la fin de l'analyse avant de passer à l'entreprise suivante (garantit la cohérence des données)

## Prochaines améliorations possibles

1. **Cache des analyses** : Mettre en cache les résultats d'analyse pour éviter de ré-analyser les mêmes emails
2. **Analyse asynchrone** : Utiliser des tâches Celery pour analyser les emails en parallèle (actuellement séquentiel)
3. **Filtrage intelligent** : Filtrer automatiquement les emails à faible score de qualité
4. **Export enrichi** : Exporter les emails avec leurs analyses dans les fichiers Excel

