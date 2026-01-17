"""
Classe Database de base avec initialisation et connexion
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict, Optional


class DatabaseBase:
    """
    Classe de base pour la gestion de la base de données
    Contient uniquement l'initialisation et la gestion des connexions
    """
    
    def __init__(self, db_path=None):
        """Initialise la connexion à la base de données"""
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
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Obtient une connexion à la base de données"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Activer les foreign keys pour que CASCADE fonctionne
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    
    def init_database(self):
        """Initialise les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des analyses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                output_filename TEXT,
                total_entreprises INTEGER,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parametres TEXT,
                statut TEXT,
                duree_secondes REAL
            )
        ''')
        
        # Table des entreprises analysées
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analyse_id INTEGER,
                nom TEXT NOT NULL,
                website TEXT,
                secteur TEXT,
                statut TEXT,
                opportunite TEXT,
                email_principal TEXT,
                responsable TEXT,
                taille_estimee TEXT,
                hosting_provider TEXT,
                framework TEXT,
                score_securite INTEGER,
                tags TEXT,
                notes TEXT,
                favori INTEGER DEFAULT 0,
                telephone TEXT,
                pays TEXT,
                address_1 TEXT,
                address_2 TEXT,
                longitude REAL,
                latitude REAL,
                note_google REAL,
                nb_avis_google INTEGER,
                date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analyse_id) REFERENCES analyses(id) ON DELETE CASCADE
            )
        ''')
        
        # Ajouter les nouvelles colonnes si elles n'existent pas (migration)
        new_columns = [
            ('telephone', 'TEXT'),
            ('pays', 'TEXT'),
            ('address_1', 'TEXT'),
            ('address_2', 'TEXT'),
            ('longitude', 'REAL'),
            ('latitude', 'REAL'),
            ('note_google', 'REAL'),
            ('nb_avis_google', 'INTEGER')
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE entreprises ADD COLUMN {col_name} {col_type}')
            except sqlite3.OperationalError:
                pass  # La colonne existe déjà
        
        # Ajouter la colonne resume si elle n'existe pas
        try:
            cursor.execute('ALTER TABLE entreprises ADD COLUMN resume TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Ajouter les colonnes pour les images et icônes
        icon_columns = [
            ('og_image', 'TEXT'),
            ('favicon', 'TEXT'),
            ('logo', 'TEXT')
        ]
        for col_name, col_type in icon_columns:
            try:
                cursor.execute(f'ALTER TABLE entreprises ADD COLUMN {col_name} {col_type}')
            except sqlite3.OperationalError:
                pass
        
        # Table des données OpenGraph (normalisée selon ogp.me)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprise_og_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                page_url TEXT,
                og_title TEXT,
                og_type TEXT,
                og_url TEXT,
                og_description TEXT,
                og_determiner TEXT,
                og_locale TEXT,
                og_site_name TEXT,
                og_audio TEXT,
                og_video TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
            )
        ''')
        
        # Migration : ajouter la colonne page_url si elle n'existe pas
        try:
            cursor.execute('ALTER TABLE entreprise_og_data ADD COLUMN page_url TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Table des images OpenGraph
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprise_og_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                og_data_id INTEGER,
                image_url TEXT NOT NULL,
                secure_url TEXT,
                image_type TEXT,
                width INTEGER,
                height INTEGER,
                alt_text TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (og_data_id) REFERENCES entreprise_og_data(id) ON DELETE CASCADE
            )
        ''')
        
        # Table des vidéos OpenGraph
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprise_og_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                og_data_id INTEGER,
                video_url TEXT NOT NULL,
                secure_url TEXT,
                video_type TEXT,
                width INTEGER,
                height INTEGER,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (og_data_id) REFERENCES entreprise_og_data(id) ON DELETE CASCADE
            )
        ''')
        
        # Table des audios OpenGraph
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprise_og_audios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                og_data_id INTEGER,
                audio_url TEXT NOT NULL,
                secure_url TEXT,
                audio_type TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (og_data_id) REFERENCES entreprise_og_data(id) ON DELETE CASCADE
            )
        ''')
        
        # Table des locales alternatives OpenGraph
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entreprise_og_locales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                og_data_id INTEGER,
                locale TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (og_data_id) REFERENCES entreprise_og_data(id) ON DELETE CASCADE,
                UNIQUE(og_data_id, locale)
            )
        ''')
        
        # Index pour les recherches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_og_data_entreprise_id ON entreprise_og_data(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_og_images_entreprise_id ON entreprise_og_images(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_og_videos_entreprise_id ON entreprise_og_videos(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_og_audios_entreprise_id ON entreprise_og_audios(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_og_locales_entreprise_id ON entreprise_og_locales(entreprise_id)')
        
        # Table des campagnes email
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campagnes_email (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                template_id TEXT,
                sujet TEXT,
                total_destinataires INTEGER DEFAULT 0,
                total_envoyes INTEGER DEFAULT 0,
                total_reussis INTEGER DEFAULT 0,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'draft',
                CHECK (statut IN ('draft', 'running', 'completed', 'failed', 'cancelled'))
            )
        ''')
        
        # Migration: ajouter date_modification si elle n'existe pas
        try:
            cursor.execute('ALTER TABLE campagnes_email ADD COLUMN date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        except sqlite3.OperationalError:
            pass
        
        # Table des emails envoyés (normalisée - entreprise via entreprise_id uniquement)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails_envoyes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campagne_id INTEGER NOT NULL,
                entreprise_id INTEGER,
                email TEXT NOT NULL,
                nom_destinataire TEXT,
                sujet TEXT,
                date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'pending',
                erreur TEXT,
                tracking_token TEXT,
                FOREIGN KEY (campagne_id) REFERENCES campagnes_email(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE SET NULL,
                CHECK (statut IN ('pending', 'sent', 'failed', 'bounced'))
            )
        ''')
        
        # Migration: ajouter tracking_token si elle n'existe pas (pour les bases existantes)
        try:
            cursor.execute('ALTER TABLE emails_envoyes ADD COLUMN tracking_token TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Créer l'index unique sur tracking_token après la migration
        try:
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_emails_tracking_token_unique ON emails_envoyes(tracking_token) WHERE tracking_token IS NOT NULL')
        except sqlite3.OperationalError:
            pass
        
        # Table des événements de tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER NOT NULL,
                tracking_token TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                date_event TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails_envoyes(id) ON DELETE CASCADE,
                CHECK (event_type IN ('open', 'click', 'read_time', 'bounce', 'unsubscribe'))
            )
        ''')
        
        # ==================== INDEX POUR OPTIMISATION LECTURE/ÉCRITURE ====================
        
        # Index pour campagnes_email
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campagnes_statut ON campagnes_email(statut)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campagnes_date_creation ON campagnes_email(date_creation DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campagnes_date_modification ON campagnes_email(date_modification DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campagnes_statut_date ON campagnes_email(statut, date_creation DESC)')
        
        # Index pour emails_envoyes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_campagne ON emails_envoyes(campagne_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_entreprise ON emails_envoyes(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_statut ON emails_envoyes(statut)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_date_envoi ON emails_envoyes(date_envoi DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_campagne_statut ON emails_envoyes(campagne_id, statut)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_campagne_date ON emails_envoyes(campagne_id, date_envoi DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_entreprise_statut ON emails_envoyes(entreprise_id, statut)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_token ON emails_envoyes(tracking_token)')
        
        # Index pour email_tracking_events
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_email_id ON email_tracking_events(email_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_token_events ON email_tracking_events(tracking_token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_event_type ON email_tracking_events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_date_event ON email_tracking_events(date_event DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_email_type ON email_tracking_events(email_id, event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_email_date ON email_tracking_events(email_id, date_event DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracking_token_type ON email_tracking_events(tracking_token, event_type)')
        
        # Table des analyses techniques
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses_techniques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER,
                url TEXT NOT NULL,
                domain TEXT,
                ip_address TEXT,
                server_software TEXT,
                framework TEXT,
                framework_version TEXT,
                cms TEXT,
                cms_version TEXT,
                cms_plugins TEXT,
                hosting_provider TEXT,
                domain_creation_date TEXT,
                domain_updated_date TEXT,
                domain_registrar TEXT,
                ssl_valid BOOLEAN,
                ssl_expiry_date TEXT,
                security_headers TEXT,
                waf TEXT,
                cdn TEXT,
                analytics TEXT,
                seo_meta TEXT,
                performance_metrics TEXT,
                nmap_scan TEXT,
                technical_details TEXT,
                date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
            )
        ''')
        
        # Ajouter la colonne cms_version si elle n'existe pas
        try:
            cursor.execute('ALTER TABLE analyses_techniques ADD COLUMN cms_version TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Tables normalisées pour les analyses techniques
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_technique_cms_plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                plugin_name TEXT NOT NULL,
                version TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_techniques(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, plugin_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_technique_security_headers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                header_name TEXT NOT NULL,
                header_value TEXT,
                status TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_techniques(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, header_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_technique_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                tool_id TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_techniques(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, tool_name)
            )
        ''')
        
        # Colonnes complémentaires pour les analyses techniques
        for col in [
            ('pages_count', 'INTEGER'),
            ('security_score', 'INTEGER'),
            ('performance_score', 'INTEGER'),
            ('trackers_count', 'INTEGER'),
            ('pages_summary', 'TEXT')
        ]:
            try:
                cursor.execute(f'ALTER TABLE analyses_techniques ADD COLUMN {col[0]} {col[1]}')
            except sqlite3.OperationalError:
                pass
        
        # Table des pages analysées
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_technique_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                page_url TEXT NOT NULL,
                status_code INTEGER,
                final_url TEXT,
                content_type TEXT,
                title TEXT,
                response_time_ms INTEGER,
                content_length INTEGER,
                security_score INTEGER,
                performance_score INTEGER,
                trackers_count INTEGER,
                security_headers TEXT,
                analytics TEXT,
                details TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_techniques(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_cms_plugins_analysis_id ON analysis_technique_cms_plugins(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_security_headers_analysis_id ON analysis_technique_security_headers(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_analytics_analysis_id ON analysis_technique_analytics(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_url ON analyses_techniques(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_domain ON analyses_techniques(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_entreprise_date ON analyses_techniques(entreprise_id, date_analyse)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_pages_analysis_id ON analysis_technique_pages(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_pages_url ON analysis_technique_pages(page_url)')
        
        # Table des analyses OSINT
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses_osint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER,
                url TEXT NOT NULL,
                domain TEXT,
                subdomains TEXT,
                dns_records TEXT,
                whois_data TEXT,
                emails_found TEXT,
                social_media TEXT,
                technologies_detected TEXT,
                ssl_info TEXT,
                ip_info TEXT,
                shodan_data TEXT,
                censys_data TEXT,
                osint_details TEXT,
                date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
            )
        ''')
        
        # Tables normalisées pour les analyses OSINT
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_osint_subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                subdomain TEXT NOT NULL,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_osint(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, subdomain)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_osint_dns_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                record_type TEXT NOT NULL,
                record_value TEXT NOT NULL,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_osint(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_osint_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                source TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_osint(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, email)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_osint_social_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_osint(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, platform, url)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_osint_technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_osint(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, category, name)
            )
        ''')
        
        # Index pour les analyses OSINT
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_subdomains_analysis_id ON analysis_osint_subdomains(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_dns_analysis_id ON analysis_osint_dns_records(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_emails_analysis_id ON analysis_osint_emails(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_social_analysis_id ON analysis_osint_social_media(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_tech_analysis_id ON analysis_osint_technologies(analysis_id)')
        
        # Table des analyses Pentest
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses_pentest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER,
                url TEXT NOT NULL,
                domain TEXT,
                vulnerabilities TEXT,
                sql_injection TEXT,
                xss_vulnerabilities TEXT,
                csrf_vulnerabilities TEXT,
                authentication_issues TEXT,
                authorization_issues TEXT,
                sensitive_data_exposure TEXT,
                security_headers_analysis TEXT,
                ssl_tls_analysis TEXT,
                waf_detection TEXT,
                cms_vulnerabilities TEXT,
                api_security TEXT,
                network_scan TEXT,
                pentest_details TEXT,
                risk_score INTEGER,
                date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
            )
        ''')
        
        # Tables normalisées pour les analyses Pentest
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_pentest_vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                recommendation TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_pentest(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_pentest_security_headers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                header_name TEXT NOT NULL,
                status TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_pentest(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, header_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_pentest_cms_vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_pentest(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_pentest_open_ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                service TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses_pentest(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, port)
            )
        ''')
        
        # Index pour les analyses Pentest
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pentest_vuln_analysis_id ON analysis_pentest_vulnerabilities(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pentest_security_headers_analysis_id ON analysis_pentest_security_headers(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pentest_cms_vuln_analysis_id ON analysis_pentest_cms_vulnerabilities(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pentest_ports_analysis_id ON analysis_pentest_open_ports(analysis_id)')
        
        # Table des scrapers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrapers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER,
                url TEXT NOT NULL,
                scraper_type TEXT NOT NULL,
                emails TEXT,
                people TEXT,
                phones TEXT,
                social_profiles TEXT,
                technologies TEXT,
                metadata TEXT,
                visited_urls INTEGER,
                total_emails INTEGER,
                total_people INTEGER,
                total_phones INTEGER,
                total_social_profiles INTEGER,
                total_technologies INTEGER,
                total_metadata INTEGER,
                total_images INTEGER DEFAULT 0,
                total_forms INTEGER DEFAULT 0,
                duration REAL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                UNIQUE(entreprise_id, url, scraper_type)
            )
        ''')
        
        # Table des images
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER,
                scraper_id INTEGER,
                url TEXT NOT NULL,
                alt_text TEXT,
                page_url TEXT,
                width INTEGER,
                height INTEGER,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: ajouter les colonnes manquantes
        for col in [
            ('entreprise_id', 'INTEGER'),
            ('scraper_id', 'INTEGER'),
            ('total_forms', 'INTEGER DEFAULT 0'),
            ('phones', 'TEXT'),
            ('social_profiles', 'TEXT'),
            ('technologies', 'TEXT'),
            ('metadata', 'TEXT'),
            ('total_phones', 'INTEGER DEFAULT 0'),
            ('total_social_profiles', 'INTEGER DEFAULT 0'),
            ('total_technologies', 'INTEGER DEFAULT 0'),
            ('total_metadata', 'INTEGER DEFAULT 0'),
            ('total_images', 'INTEGER DEFAULT 0'),
            ('date_creation', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('date_modification', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]:
            try:
                cursor.execute(f'ALTER TABLE scrapers ADD COLUMN {col[0]} {col[1]}')
            except:
                pass
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_entreprise_id ON images(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_scraper_id ON images(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_url ON images(url)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_images_entreprise_url ON images(entreprise_id, url)')
        
        # Tables normalisées pour les données des scrapers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                page_url TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                UNIQUE(scraper_id, email)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                page_url TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                UNIQUE(scraper_id, phone)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_social_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                page_url TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                UNIQUE(scraper_id, platform, url)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                page_url TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                UNIQUE(scraper_id, category, name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                person_id INTEGER,
                name TEXT,
                title TEXT,
                email TEXT,
                linkedin_url TEXT,
                page_url TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (person_id) REFERENCES personnes(id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraper_id INTEGER NOT NULL,
                entreprise_id INTEGER NOT NULL,
                page_url TEXT NOT NULL,
                action_url TEXT,
                method TEXT DEFAULT 'GET',
                enctype TEXT,
                has_csrf INTEGER DEFAULT 0,
                has_file_upload INTEGER DEFAULT 0,
                fields_count INTEGER DEFAULT 0,
                fields_data TEXT,
                date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scraper_id) REFERENCES scrapers(id) ON DELETE CASCADE,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_emails_scraper_id ON scraper_emails(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_emails_entreprise_id ON scraper_emails(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_phones_scraper_id ON scraper_phones(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_phones_entreprise_id ON scraper_phones(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_social_scraper_id ON scraper_social_profiles(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_social_entreprise_id ON scraper_social_profiles(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_tech_scraper_id ON scraper_technologies(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_tech_entreprise_id ON scraper_technologies(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_people_scraper_id ON scraper_people(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_people_entreprise_id ON scraper_people(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_forms_scraper_id ON scraper_forms(scraper_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_forms_entreprise_id ON scraper_forms(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraper_forms_page_url ON scraper_forms(page_url)')
        
        # Table des personnes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personnes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT,
                titre TEXT,
                role TEXT,
                email TEXT,
                telephone TEXT,
                linkedin_url TEXT,
                linkedin_profile_data TEXT,
                social_profiles TEXT,
                osint_data TEXT,
                niveau_hierarchique INTEGER,
                manager_id INTEGER,
                source TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_mise_a_jour TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE,
                FOREIGN KEY (manager_id) REFERENCES personnes(id) ON DELETE SET NULL
            )
        ''')
        
        # Index pour performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entreprises_analyse ON entreprises(analyse_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entreprises_nom ON entreprises(nom)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entreprises_secteur ON entreprises(secteur)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entreprises_geo ON entreprises(longitude, latitude)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tech_entreprise ON analyses_techniques(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_osint_entreprise ON analyses_osint(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pentest_entreprise ON analyses_pentest(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapers_entreprise ON scrapers(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapers_url ON scrapers(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_personnes_entreprise ON personnes(entreprise_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_personnes_manager ON personnes(manager_id)')
        
        conn.commit()
        conn.close()
        
        # Migration : recréer les contraintes avec ON DELETE CASCADE si nécessaire
        self.migrate_foreign_keys_cascade()
    
    def migrate_foreign_keys_cascade(self):
        """Active les clés étrangères pour SQLite"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('PRAGMA foreign_keys = ON')
            conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()

