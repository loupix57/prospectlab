"""
Module pour la gestion des analyses dans la base de données
"""

import json
import sqlite3


class AnalysesMixin:
    """
    Mixin pour les méthodes de gestion des analyses
    """

    def save_technical_analysis(self, entreprise_id, url, tech_data):
        """Sauvegarde une analyse technique avec normalisation des données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Extraire le domaine de l'URL
        domain = url.replace('http://', '').replace('https://', '').split('/')[0].replace('www.', '')
        
        pages_summary = tech_data.get('pages_summary') or {}
        pages = tech_data.get('pages') or []
        security_score = tech_data.get('security_score')
        performance_score = tech_data.get('performance_score')
        trackers_count = tech_data.get('trackers_count')
        pages_count = tech_data.get('pages_count') or (len(pages) if pages else None)

        # Sauvegarder l'analyse principale (sans les données JSON normalisées)
        # Colonnes: entreprise_id, url, domain, ip_address, server_software, framework, framework_version,
        # cms, cms_version, cms_plugins, hosting_provider, domain_creation_date, domain_updated_date,
        # domain_registrar, ssl_valid, ssl_expiry_date, security_headers, waf, cdn, analytics,
        # seo_meta, performance_metrics, nmap_scan, technical_details, pages_count, security_score,
        # performance_score, trackers_count, pages_summary (29 colonnes au total)
        cursor.execute('''
            INSERT INTO analyses_techniques (
                entreprise_id, url, domain, ip_address, server_software,
                framework, framework_version, cms, cms_version, cms_plugins, hosting_provider,
                domain_creation_date, domain_updated_date, domain_registrar,
                ssl_valid, ssl_expiry_date, security_headers, waf, cdn, analytics,
                seo_meta, performance_metrics, nmap_scan, technical_details,
                pages_count, security_score, performance_score, trackers_count, pages_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entreprise_id,
            url,
            domain,
            tech_data.get('ip_address'),
            tech_data.get('server_software'),
            tech_data.get('framework'),
            tech_data.get('framework_version'),
            tech_data.get('cms'),
            tech_data.get('cms_version'),
            json.dumps(tech_data.get('cms_plugins', [])) if tech_data.get('cms_plugins') else None,
            tech_data.get('hosting_provider'),
            tech_data.get('domain_creation_date'),
            tech_data.get('domain_updated_date'),
            tech_data.get('domain_registrar'),
            tech_data.get('ssl_valid'),
            tech_data.get('ssl_expiry_date'),
            json.dumps(tech_data.get('security_headers', {})) if tech_data.get('security_headers') else None,
            tech_data.get('waf'),
            tech_data.get('cdn'),
            json.dumps(tech_data.get('analytics', {})) if tech_data.get('analytics') else None,
            json.dumps(tech_data.get('seo_meta', {})) if tech_data.get('seo_meta') else None,
            json.dumps(tech_data.get('performance_metrics', {})) if tech_data.get('performance_metrics') else None,
            json.dumps(tech_data.get('nmap_scan', {})) if tech_data.get('nmap_scan') else None,
            json.dumps(tech_data) if tech_data else None,
            pages_count,
            security_score,
            performance_score,
            trackers_count,
            json.dumps(pages_summary) if pages_summary else None
        ))
        
        analysis_id = cursor.lastrowid
        
        # Sauvegarder les plugins CMS dans la table normalisée
        cms_plugins = tech_data.get('cms_plugins', [])
        if cms_plugins:
            if isinstance(cms_plugins, str):
                try:
                    cms_plugins = json.loads(cms_plugins)
                except:
                    cms_plugins = []
            if isinstance(cms_plugins, list):
                for plugin in cms_plugins:
                    if isinstance(plugin, dict):
                        plugin_name = plugin.get('name') or plugin.get('plugin') or str(plugin)
                        plugin_version = plugin.get('version')
                    else:
                        plugin_name = str(plugin)
                        plugin_version = None
                    if plugin_name:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_technique_cms_plugins (analysis_id, plugin_name, version)
                            VALUES (?, ?, ?)
                        ''', (analysis_id, plugin_name, plugin_version))
        
        # Sauvegarder les headers de sécurité dans la table normalisée
        security_headers = tech_data.get('security_headers', {})
        if security_headers:
            if isinstance(security_headers, str):
                try:
                    security_headers = json.loads(security_headers)
                except:
                    security_headers = {}
            if isinstance(security_headers, dict):
                for header_name, header_data in security_headers.items():
                    if isinstance(header_data, dict):
                        header_value = header_data.get('value') or header_data.get('header')
                        status = header_data.get('status') or header_data.get('present')
                    else:
                        header_value = str(header_data) if header_data else None
                        status = 'present' if header_data else None
                    cursor.execute('''
                        INSERT OR REPLACE INTO analysis_technique_security_headers (analysis_id, header_name, header_value, status)
                        VALUES (?, ?, ?, ?)
                    ''', (analysis_id, header_name, header_value, status))
        
        # Sauvegarder les outils d'analytics dans la table normalisée
        analytics = tech_data.get('analytics', [])
        if analytics:
            if isinstance(analytics, str):
                try:
                    analytics = json.loads(analytics)
                except:
                    analytics = []
            if isinstance(analytics, list):
                for tool in analytics:
                    if isinstance(tool, dict):
                        tool_name = tool.get('name') or tool.get('tool') or str(tool)
                        tool_id = tool.get('id') or tool.get('tracking_id')
                    else:
                        tool_name = str(tool)
                        tool_id = None
                    if tool_name:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_technique_analytics (analysis_id, tool_name, tool_id)
                            VALUES (?, ?, ?)
                        ''', (analysis_id, tool_name, tool_id))

        # Sauvegarder les pages analysées (multi-pages)
        if pages:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Sauvegarde de {len(pages)} page(s) pour l\'analyse technique {analysis_id}')
            for page in pages:
                try:
                    page_url = page.get('url') or page.get('page_url')
                    if not page_url:
                        logger.warning(f'Page sans URL ignorée: {page}')
                        continue
                    cursor.execute('''
                        INSERT INTO analysis_technique_pages (
                            analysis_id, page_url, status_code, final_url, content_type,
                            title, response_time_ms, content_length, security_score,
                            performance_score, trackers_count, security_headers, analytics, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        analysis_id,
                        page_url,
                        page.get('status_code'),
                        page.get('final_url'),
                        page.get('content_type'),
                        page.get('title'),
                        page.get('response_time_ms'),
                        page.get('content_length'),
                        page.get('security_score'),
                        page.get('performance_score'),
                        page.get('trackers_count'),
                        json.dumps(page.get('security_headers')) if page.get('security_headers') else None,
                        json.dumps(page.get('analytics')) if page.get('analytics') else None,
                        json.dumps(page) if page else None
                    ))
                except Exception as e:
                    logger.error(f'Erreur lors de la sauvegarde d\'une page pour l\'analyse {analysis_id}: {e}', exc_info=True)
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Aucune page à sauvegarder pour l\'analyse technique {analysis_id} (pages={pages})')

        # Mettre à jour la fiche entreprise avec le score de sécurité global si présent
        if entreprise_id and security_score is not None:
            try:
                cursor.execute(
                    'UPDATE entreprises SET score_securite = ? WHERE id = ?',
                    (security_score, entreprise_id)
                )
            except Exception:
                pass
        
        conn.commit()
        conn.close()
        
        return analysis_id
    

    def _load_technical_analysis_normalized_data(self, cursor, analysis_id):
        """Charge les données normalisées d'une analyse technique"""
        # Charger les plugins CMS
        cursor.execute('''
            SELECT plugin_name, version FROM analysis_technique_cms_plugins
            WHERE analysis_id = ?
        ''', (analysis_id,))
        plugins = []
        for plugin_row in cursor.fetchall():
            plugin = {'name': plugin_row['plugin_name']}
            if plugin_row['version']:
                plugin['version'] = plugin_row['version']
            plugins.append(plugin)
        
        # Charger les headers de sécurité
        cursor.execute('''
            SELECT header_name, header_value, status FROM analysis_technique_security_headers
            WHERE analysis_id = ?
        ''', (analysis_id,))
        headers = {}
        for header_row in cursor.fetchall():
            headers[header_row['header_name']] = {
                'value': header_row['header_value'],
                'status': header_row['status']
            }
        
        # Charger les outils d'analytics
        cursor.execute('''
            SELECT tool_name, tool_id FROM analysis_technique_analytics
            WHERE analysis_id = ?
        ''', (analysis_id,))
        analytics = []
        for analytics_row in cursor.fetchall():
            tool = {'name': analytics_row['tool_name']}
            if analytics_row['tool_id']:
                tool['id'] = analytics_row['tool_id']
            analytics.append(tool)

        # Charger les pages analysées (multi-pages)
        cursor.execute('''
            SELECT * FROM analysis_technique_pages
            WHERE analysis_id = ?
            ORDER BY id ASC
        ''', (analysis_id,))
        pages = []
        for page_row in cursor.fetchall():
            page_data = dict(page_row)
            for json_field in ['security_headers', 'analytics', 'details']:
                if page_data.get(json_field):
                    try:
                        page_data[json_field] = json.loads(page_data[json_field])
                    except Exception:
                        pass
            pages.append(page_data)
        
        return {
            'cms_plugins': plugins,
            'security_headers': headers,
            'analytics': analytics,
            'pages': pages
        }
    

    def get_technical_analysis(self, entreprise_id):
        """Récupère l'analyse technique d'une entreprise avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analyses_techniques
            WHERE entreprise_id = ?
            ORDER BY date_analyse DESC
            LIMIT 1
        ''', (entreprise_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_technical_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            for field in ['seo_meta', 'performance_metrics', 'nmap_scan', 'technical_details', 'pages_summary']:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_all_technical_analyses(self, limit=100):
        """Récupère toutes les analyses techniques avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT at.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_techniques at
            LEFT JOIN entreprises e ON at.entreprise_id = e.id
            ORDER BY at.date_analyse DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        analyses = []
        for row in rows:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_technical_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            for field in ['seo_meta', 'performance_metrics', 'nmap_scan', 'technical_details', 'pages_summary']:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            analyses.append(analysis)
        
        conn.close()
        return analyses
    

    def get_technical_analysis_by_id(self, analysis_id):
        """Récupère une analyse technique par son ID avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT at.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_techniques at
            LEFT JOIN entreprises e ON at.entreprise_id = e.id
            WHERE at.id = ?
        ''', (analysis_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_technical_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            for field in ['seo_meta', 'performance_metrics', 'nmap_scan', 'technical_details', 'pages_summary']:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_technical_analysis_by_url(self, url):
        """Récupère une analyse technique par son URL avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT at.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_techniques at
            LEFT JOIN entreprises e ON at.entreprise_id = e.id
            WHERE at.url = ?
            ORDER BY at.date_analyse DESC
            LIMIT 1
        ''', (url,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_technical_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            for field in ['seo_meta', 'performance_metrics', 'nmap_scan', 'technical_details', 'pages_summary']:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def update_technical_analysis(self, analysis_id, tech_data):
        """Met à jour une analyse technique avec normalisation"""
        conn = self.get_connection()
        cursor = conn.cursor()

        pages_summary = tech_data.get('pages_summary') or {}
        pages = tech_data.get('pages') or []
        security_score = tech_data.get('security_score')
        performance_score = tech_data.get('performance_score')
        trackers_count = tech_data.get('trackers_count')
        pages_count = tech_data.get('pages_count') or (len(pages) if pages else None)

        # Récupérer entreprise_id + url existants (on conserve le même id)
        cursor.execute('SELECT entreprise_id, url FROM analyses_techniques WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return analysis_id

        entreprise_id = row['entreprise_id']
        url = row['url'] or tech_data.get('url', '')

        # Mettre à jour la ligne principale (évite de casser les références et garde un historique cohérent)
        domain = url.replace('http://', '').replace('https://', '').split('/')[0].replace('www.', '')
        cursor.execute('''
            UPDATE analyses_techniques
            SET url = ?,
                domain = ?,
                ip_address = ?,
                server_software = ?,
                framework = ?,
                framework_version = ?,
                cms = ?,
                cms_version = ?,
                hosting_provider = ?,
                domain_creation_date = ?,
                domain_updated_date = ?,
                domain_registrar = ?,
                ssl_valid = ?,
                ssl_expiry_date = ?,
                waf = ?,
                cdn = ?,
                seo_meta = ?,
                performance_metrics = ?,
                nmap_scan = ?,
                technical_details = ?,
                pages_count = ?,
                security_score = ?,
                performance_score = ?,
                trackers_count = ?,
                pages_summary = ?,
                date_analyse = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            url,
            domain,
            tech_data.get('ip_address'),
            tech_data.get('server_software'),
            tech_data.get('framework'),
            tech_data.get('framework_version'),
            tech_data.get('cms'),
            tech_data.get('cms_version'),
            tech_data.get('hosting_provider'),
            tech_data.get('domain_creation_date'),
            tech_data.get('domain_updated_date'),
            tech_data.get('domain_registrar'),
            tech_data.get('ssl_valid'),
            tech_data.get('ssl_expiry_date'),
            tech_data.get('waf'),
            tech_data.get('cdn'),
            json.dumps(tech_data.get('seo_meta', {})) if tech_data.get('seo_meta') else None,
            json.dumps(tech_data.get('performance_metrics', {})) if tech_data.get('performance_metrics') else None,
            json.dumps(tech_data.get('nmap_scan', {})) if tech_data.get('nmap_scan') else None,
            json.dumps(tech_data) if tech_data else None,
            pages_count,
            security_score,
            performance_score,
            trackers_count,
            json.dumps(pages_summary) if pages_summary else None,
            analysis_id
        ))

        # Supprimer puis réinsérer les données normalisées
        cursor.execute('DELETE FROM analysis_technique_cms_plugins WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_technique_security_headers WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_technique_analytics WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_technique_pages WHERE analysis_id = ?', (analysis_id,))

        # Plugins CMS
        cms_plugins = tech_data.get('cms_plugins', [])
        if cms_plugins:
            if isinstance(cms_plugins, str):
                try:
                    cms_plugins = json.loads(cms_plugins)
                except:
                    cms_plugins = []
            if isinstance(cms_plugins, list):
                for plugin in cms_plugins:
                    if isinstance(plugin, dict):
                        plugin_name = plugin.get('name') or plugin.get('plugin') or str(plugin)
                        plugin_version = plugin.get('version')
                    else:
                        plugin_name = str(plugin)
                        plugin_version = None
                    if plugin_name:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_technique_cms_plugins (analysis_id, plugin_name, version)
                            VALUES (?, ?, ?)
                        ''', (analysis_id, plugin_name, plugin_version))

        # Headers de sécurité
        security_headers = tech_data.get('security_headers', {})
        if security_headers:
            if isinstance(security_headers, str):
                try:
                    security_headers = json.loads(security_headers)
                except:
                    security_headers = {}
            if isinstance(security_headers, dict):
                for header_name, header_data in security_headers.items():
                    if isinstance(header_data, dict):
                        header_value = header_data.get('value') or header_data.get('header')
                        status = header_data.get('status') or header_data.get('present')
                    else:
                        header_value = str(header_data) if header_data else None
                        status = 'present' if header_data else None
                    cursor.execute('''
                        INSERT OR REPLACE INTO analysis_technique_security_headers (analysis_id, header_name, header_value, status)
                        VALUES (?, ?, ?, ?)
                    ''', (analysis_id, header_name, header_value, status))

        # Analytics
        analytics = tech_data.get('analytics', [])
        if analytics:
            if isinstance(analytics, str):
                try:
                    analytics = json.loads(analytics)
                except:
                    analytics = []
            if isinstance(analytics, list):
                for tool in analytics:
                    if isinstance(tool, dict):
                        tool_name = tool.get('name') or tool.get('tool') or str(tool)
                        tool_id = tool.get('id') or tool.get('tracking_id')
                    else:
                        tool_name = str(tool)
                        tool_id = None
                    if tool_name:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_technique_analytics (analysis_id, tool_name, tool_id)
                            VALUES (?, ?, ?)
                        ''', (analysis_id, tool_name, tool_id))

        # Pages multi-analysées
        if pages:
            for page in pages:
                cursor.execute('''
                    INSERT INTO analysis_technique_pages (
                        analysis_id, page_url, status_code, final_url, content_type,
                        title, response_time_ms, content_length, security_score,
                        performance_score, trackers_count, security_headers, analytics, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    page.get('url') or page.get('page_url'),
                    page.get('status_code'),
                    page.get('final_url'),
                    page.get('content_type'),
                    page.get('title'),
                    page.get('response_time_ms'),
                    page.get('content_length'),
                    page.get('security_score'),
                    page.get('performance_score'),
                    page.get('trackers_count'),
                    json.dumps(page.get('security_headers')) if page.get('security_headers') else None,
                    json.dumps(page.get('analytics')) if page.get('analytics') else None,
                    json.dumps(page) if page else None
                ))

        # Mettre à jour la fiche entreprise avec le score global
        if security_score is not None and entreprise_id:
            try:
                cursor.execute(
                    'UPDATE entreprises SET score_securite = ? WHERE id = ?',
                    (security_score, entreprise_id)
                )
            except Exception:
                pass

        conn.commit()
        conn.close()
        return analysis_id
    

    def delete_technical_analysis(self, analysis_id):
        """Supprime une analyse technique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analyses_techniques WHERE id = ?', (analysis_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    

    def save_osint_analysis(self, entreprise_id, url, osint_data):
        """Sauvegarde une analyse OSINT avec normalisation des données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        domain_clean = domain.replace('www.', '') if domain else ''
        
        # Sauvegarder l'analyse principale (sans les données JSON normalisées)
        cursor.execute('''
            INSERT INTO analyses_osint (
                entreprise_id, url, domain, whois_data,
                ssl_info, ip_info, shodan_data, censys_data, osint_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entreprise_id,
            url,
            domain_clean,
            json.dumps(osint_data.get('whois_info', {})) if osint_data.get('whois_info') else None,
            json.dumps(osint_data.get('ssl_info', {})) if osint_data.get('ssl_info') else None,
            json.dumps(osint_data.get('ip_info', {})) if osint_data.get('ip_info') else None,
            json.dumps(osint_data.get('shodan_data', {})) if osint_data.get('shodan_data') else None,
            json.dumps(osint_data.get('censys_data', {})) if osint_data.get('censys_data') else None,
            json.dumps(osint_data) if osint_data else None
        ))
        
        analysis_id = cursor.lastrowid
        
        # Sauvegarder les sous-domaines dans la table normalisée
        subdomains = osint_data.get('subdomains', [])
        if subdomains:
            if isinstance(subdomains, str):
                try:
                    subdomains = json.loads(subdomains)
                except:
                    subdomains = []
            if isinstance(subdomains, list):
                for subdomain in subdomains:
                    subdomain_str = str(subdomain).strip()
                    if subdomain_str:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_osint_subdomains (analysis_id, subdomain)
                            VALUES (?, ?)
                        ''', (analysis_id, subdomain_str))
        
        # Sauvegarder les enregistrements DNS dans la table normalisée
        dns_records = osint_data.get('dns_records', {})
        if dns_records:
            if isinstance(dns_records, str):
                try:
                    dns_records = json.loads(dns_records)
                except:
                    dns_records = {}
            if isinstance(dns_records, dict):
                for record_type, records in dns_records.items():
                    if not isinstance(records, list):
                        records = [records]
                    for record_value in records:
                        record_value_str = str(record_value).strip()
                        if record_value_str:
                            cursor.execute('''
                                INSERT INTO analysis_osint_dns_records (analysis_id, record_type, record_value)
                                VALUES (?, ?, ?)
                            ''', (analysis_id, record_type, record_value_str))
        
        # Sauvegarder les emails dans la table normalisée
        emails = osint_data.get('emails', [])
        if emails:
            if isinstance(emails, str):
                try:
                    emails = json.loads(emails)
                except:
                    emails = []
            if isinstance(emails, list):
                for email in emails:
                    if isinstance(email, dict):
                        email_str = email.get('email') or email.get('value') or str(email)
                        source = email.get('source')
                    else:
                        email_str = str(email).strip()
                        source = None
                    if email_str:
                        cursor.execute('''
                            INSERT OR IGNORE INTO analysis_osint_emails (analysis_id, email, source)
                            VALUES (?, ?, ?)
                        ''', (analysis_id, email_str, source))
        
        # Sauvegarder les réseaux sociaux dans la table normalisée
        social_media = osint_data.get('social_media', {})
        if not social_media and osint_data.get('people'):
            # Si les personnes sont dans 'people', extraire leurs réseaux sociaux
            people = osint_data.get('people', {})
            if isinstance(people, dict):
                for person_data in people.values():
                    if isinstance(person_data, dict) and person_data.get('social_profiles'):
                        if not social_media:
                            social_media = {}
                        for platform, url_social in person_data.get('social_profiles', {}).items():
                            if platform not in social_media:
                                social_media[platform] = []
                            if url_social not in social_media[platform]:
                                social_media[platform].append(url_social)
        
        if social_media:
            if isinstance(social_media, str):
                try:
                    social_media = json.loads(social_media)
                except:
                    social_media = {}
            if isinstance(social_media, dict):
                for platform, urls in social_media.items():
                    if not isinstance(urls, list):
                        urls = [urls]
                    for url_social in urls:
                        url_social_str = str(url_social).strip()
                        if url_social_str:
                            cursor.execute('''
                                INSERT OR IGNORE INTO analysis_osint_social_media (analysis_id, platform, url)
                                VALUES (?, ?, ?)
                            ''', (analysis_id, platform, url_social_str))
        
        # Sauvegarder les technologies dans la table normalisée
        technologies = osint_data.get('technologies', {})
        if technologies:
            if isinstance(technologies, str):
                try:
                    technologies = json.loads(technologies)
                except:
                    technologies = {}
            if isinstance(technologies, dict):
                for category, techs in technologies.items():
                    if not isinstance(techs, list):
                        techs = [techs]
                    for tech in techs:
                        tech_name = str(tech).strip()
                        if tech_name:
                            cursor.execute('''
                                INSERT OR IGNORE INTO analysis_osint_technologies (analysis_id, category, name)
                                VALUES (?, ?, ?)
                            ''', (analysis_id, category, tech_name))
        
        conn.commit()
        conn.close()
        
        return analysis_id
    

    def update_osint_analysis(self, analysis_id, osint_data):
        """Met à jour une analyse OSINT existante avec normalisation"""
        # Supprimer les anciennes données normalisées
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM analysis_osint_subdomains WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_osint_dns_records WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_osint_emails WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_osint_social_media WHERE analysis_id = ?', (analysis_id,))
        cursor.execute('DELETE FROM analysis_osint_technologies WHERE analysis_id = ?', (analysis_id,))
        conn.commit()
        conn.close()
        
        # Réutiliser save_osint_analysis qui gère déjà la normalisation
        # Mais d'abord récupérer l'entreprise_id et l'url
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT entreprise_id, url FROM analyses_osint WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            entreprise_id = row['entreprise_id']
            url = row['url'] or osint_data.get('url', '')
            # Supprimer l'ancienne analyse et en créer une nouvelle
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM analyses_osint WHERE id = ?', (analysis_id,))
            conn.commit()
            conn.close()
            # Sauvegarder avec la nouvelle méthode normalisée
            return self.save_osint_analysis(entreprise_id, url, osint_data)
        
        return analysis_id
    

    def get_osint_analysis_by_entreprise(self, entreprise_id):
        """Récupère l'analyse OSINT d'une entreprise avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analyses_osint
            WHERE entreprise_id = ?
            ORDER BY date_analyse DESC
            LIMIT 1
        ''', (entreprise_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_osint_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            json_fields = ['whois_data', 'ssl_info', 'ip_info', 'shodan_data', 'censys_data', 'osint_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            # Normaliser les noms de champs pour le frontend
            if 'whois_data' in analysis:
                analysis['whois_info'] = analysis['whois_data']
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_osint_analysis_by_url(self, url):
        """Récupère une analyse OSINT par son URL avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ao.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_osint ao
            LEFT JOIN entreprises e ON ao.entreprise_id = e.id
            WHERE ao.url = ?
            ORDER BY ao.date_analyse DESC
            LIMIT 1
        ''', (url,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_osint_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            json_fields = ['whois_data', 'ssl_info', 'ip_info', 'shodan_data', 'censys_data', 'osint_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            # Normaliser les noms de champs pour le frontend
            if 'whois_data' in analysis:
                analysis['whois_info'] = analysis['whois_data']
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_osint_analysis(self, analysis_id):
        """Récupère une analyse OSINT par ID avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ao.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_osint ao
            LEFT JOIN entreprises e ON ao.entreprise_id = e.id
            WHERE ao.id = ?
        ''', (analysis_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            
            # Charger les données normalisées
            normalized = self._load_osint_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Parser les autres champs JSON
            json_fields = ['whois_data', 'ssl_info', 'ip_info', 'shodan_data', 'censys_data', 'osint_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            # Normaliser les noms de champs pour le frontend
            if 'whois_data' in analysis:
                analysis['whois_info'] = analysis['whois_data']
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_all_osint_analyses(self):
        """Récupère toutes les analyses OSINT avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ao.*, e.nom as entreprise_nom
            FROM analyses_osint ao
            LEFT JOIN entreprises e ON ao.entreprise_id = e.id
            ORDER BY ao.date_analyse DESC
        ''')
        
        rows = cursor.fetchall()
        
        analyses = []
        for row in rows:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_osint_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Ajouter les compteurs pour compatibilité
            analysis['subdomains_count'] = len(analysis.get('subdomains', []))
            analysis['emails_count'] = len(analysis.get('emails', []))
            
            analyses.append(analysis)
        
        conn.close()
        return analyses
    

    def delete_osint_analysis(self, analysis_id):
        """Supprime une analyse OSINT"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analyses_osint WHERE id = ?', (analysis_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    

    def _load_osint_analysis_normalized_data(self, cursor, analysis_id):
        """Charge les données normalisées d'une analyse OSINT"""
        # Charger les sous-domaines
        cursor.execute('SELECT subdomain FROM analysis_osint_subdomains WHERE analysis_id = ?', (analysis_id,))
        subdomains = [row['subdomain'] for row in cursor.fetchall()]
        
        # Charger les enregistrements DNS
        cursor.execute('SELECT record_type, record_value FROM analysis_osint_dns_records WHERE analysis_id = ?', (analysis_id,))
        dns_records = {}
        for row in cursor.fetchall():
            record_type = row['record_type']
            if record_type not in dns_records:
                dns_records[record_type] = []
            dns_records[record_type].append(row['record_value'])
        
        # Charger les emails
        cursor.execute('SELECT email, source FROM analysis_osint_emails WHERE analysis_id = ?', (analysis_id,))
        emails = []
        for row in cursor.fetchall():
            email = {'email': row['email']}
            if row['source']:
                email['source'] = row['source']
            emails.append(email)
        
        # Charger les réseaux sociaux
        cursor.execute('SELECT platform, url FROM analysis_osint_social_media WHERE analysis_id = ?', (analysis_id,))
        social_media = {}
        for row in cursor.fetchall():
            platform = row['platform']
            if platform not in social_media:
                social_media[platform] = []
            social_media[platform].append(row['url'])
        
        # Charger les technologies
        cursor.execute('SELECT category, name FROM analysis_osint_technologies WHERE analysis_id = ?', (analysis_id,))
        technologies = {}
        for row in cursor.fetchall():
            category = row['category']
            if category not in technologies:
                technologies[category] = []
            technologies[category].append(row['name'])
        
        return {
            'subdomains': subdomains,
            'dns_records': dns_records,
            'emails': emails,
            'emails_found': emails,  # Compatibilité
            'social_media': social_media,
            'technologies_detected': technologies,
            'technologies': technologies  # Compatibilité
        }
    

    def save_pentest_analysis(self, entreprise_id, url, pentest_data):
        """Sauvegarde une analyse Pentest avec normalisation des données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        domain_clean = domain.replace('www.', '') if domain else ''
        
        # Sauvegarder l'analyse principale (sans les données JSON normalisées)
        cursor.execute('''
            INSERT INTO analyses_pentest (
                entreprise_id, url, domain, sql_injection, xss_vulnerabilities,
                csrf_vulnerabilities, authentication_issues, authorization_issues,
                sensitive_data_exposure, ssl_tls_analysis,
                waf_detection, api_security, network_scan,
                pentest_details, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entreprise_id,
            url,
            domain_clean,
            json.dumps(pentest_data.get('sql_injection', {})) if pentest_data.get('sql_injection') else None,
            json.dumps(pentest_data.get('xss_vulnerabilities', [])) if pentest_data.get('xss_vulnerabilities') else None,
            json.dumps(pentest_data.get('csrf_vulnerabilities', [])) if pentest_data.get('csrf_vulnerabilities') else None,
            json.dumps(pentest_data.get('authentication_issues', [])) if pentest_data.get('authentication_issues') else None,
            json.dumps(pentest_data.get('authorization_issues', [])) if pentest_data.get('authorization_issues') else None,
            json.dumps(pentest_data.get('sensitive_data_exposure', [])) if pentest_data.get('sensitive_data_exposure') else None,
            json.dumps(pentest_data.get('ssl_tls', {})) if pentest_data.get('ssl_tls') else None,
            json.dumps(pentest_data.get('waf_detection', {})) if pentest_data.get('waf_detection') else None,
            json.dumps(pentest_data.get('api_security', {})) if pentest_data.get('api_security') else None,
            json.dumps(pentest_data.get('network_scan', {})) if pentest_data.get('network_scan') else None,
            json.dumps(pentest_data) if pentest_data else None,
            pentest_data.get('risk_score', 0)
        ))
        
        analysis_id = cursor.lastrowid
        
        # Sauvegarder les vulnérabilités dans la table normalisée
        vulnerabilities = pentest_data.get('vulnerabilities', [])
        if vulnerabilities:
            if isinstance(vulnerabilities, str):
                try:
                    vulnerabilities = json.loads(vulnerabilities)
                except:
                    vulnerabilities = []
            if isinstance(vulnerabilities, list):
                for vuln in vulnerabilities:
                    if isinstance(vuln, dict):
                        name = vuln.get('name') or vuln.get('title') or str(vuln)
                        severity = vuln.get('severity') or vuln.get('level')
                        description = vuln.get('description')
                        recommendation = vuln.get('recommendation') or vuln.get('fix')
                    else:
                        name = str(vuln)
                        severity = None
                        description = None
                        recommendation = None
                    if name:
                        cursor.execute('''
                            INSERT INTO analysis_pentest_vulnerabilities (analysis_id, name, severity, description, recommendation)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (analysis_id, name, severity, description, recommendation))
        
        # Sauvegarder les headers de sécurité dans la table normalisée
        security_headers = pentest_data.get('security_headers', {})
        if security_headers:
            if isinstance(security_headers, str):
                try:
                    security_headers = json.loads(security_headers)
                except:
                    security_headers = {}
            if isinstance(security_headers, dict):
                for header_name, header_data in security_headers.items():
                    if isinstance(header_data, dict):
                        status = header_data.get('status') or header_data.get('present')
                    else:
                        status = 'present' if header_data else 'missing'
                    cursor.execute('''
                        INSERT OR REPLACE INTO analysis_pentest_security_headers (analysis_id, header_name, status)
                        VALUES (?, ?, ?)
                    ''', (analysis_id, header_name, status))
        
        # Sauvegarder les vulnérabilités CMS dans la table normalisée
        cms_vulnerabilities = pentest_data.get('cms_vulnerabilities', {})
        if cms_vulnerabilities:
            if isinstance(cms_vulnerabilities, str):
                try:
                    cms_vulnerabilities = json.loads(cms_vulnerabilities)
                except:
                    cms_vulnerabilities = {}
            if isinstance(cms_vulnerabilities, dict):
                for vuln_name, vuln_data in cms_vulnerabilities.items():
                    if isinstance(vuln_data, dict):
                        severity = vuln_data.get('severity') or vuln_data.get('level')
                        description = vuln_data.get('description')
                    else:
                        severity = None
                        description = str(vuln_data) if vuln_data else None
                    cursor.execute('''
                        INSERT INTO analysis_pentest_cms_vulnerabilities (analysis_id, name, severity, description)
                        VALUES (?, ?, ?, ?)
                    ''', (analysis_id, vuln_name, severity, description))
        
        # Sauvegarder les ports ouverts dans la table normalisée
        network_scan = pentest_data.get('network_scan', {})
        if network_scan:
            if isinstance(network_scan, str):
                try:
                    network_scan = json.loads(network_scan)
                except:
                    network_scan = {}
            if isinstance(network_scan, dict):
                open_ports = network_scan.get('open_ports', [])
                if not open_ports and network_scan.get('ports'):
                    open_ports = network_scan.get('ports', [])
                if isinstance(open_ports, list):
                    for port_data in open_ports:
                        if isinstance(port_data, dict):
                            port = port_data.get('port') or port_data.get('number')
                            service = port_data.get('service') or port_data.get('name')
                        else:
                            port = int(port_data) if isinstance(port_data, (int, str)) and str(port_data).isdigit() else None
                            service = None
                        if port:
                            cursor.execute('''
                                INSERT OR IGNORE INTO analysis_pentest_open_ports (analysis_id, port, service)
                                VALUES (?, ?, ?)
                            ''', (analysis_id, port, service))
        
        conn.commit()
        conn.close()
        
        return analysis_id
    

    def update_pentest_analysis(self, analysis_id, pentest_data):
        """Met à jour une analyse Pentest existante"""
        # Supprimer l'ancienne analyse et en créer une nouvelle
        # (plus simple que de mettre à jour toutes les tables normalisées)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Récupérer l'entreprise_id et l'URL de l'analyse existante
        cursor.execute('SELECT entreprise_id, url FROM analyses_pentest WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        entreprise_id = row[0]
        url = row[1]
        
        # Supprimer l'ancienne analyse (les CASCADE supprimeront les données normalisées)
        cursor.execute('DELETE FROM analyses_pentest WHERE id = ?', (analysis_id,))
        
        conn.commit()
        conn.close()
        
        # Créer une nouvelle analyse avec les mêmes données
        return self.save_pentest_analysis(entreprise_id, url, pentest_data)
    

    def get_pentest_analysis_by_entreprise(self, entreprise_id):
        """Récupère l'analyse Pentest d'une entreprise avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analyses_pentest
            WHERE entreprise_id = ?
            ORDER BY date_analyse DESC
            LIMIT 1
        ''', (entreprise_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_pentest_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Ajouter les ports ouverts au network_scan si présent
            if 'network_scan' in analysis and analysis['network_scan']:
                try:
                    network_scan = json.loads(analysis['network_scan']) if isinstance(analysis['network_scan'], str) else analysis['network_scan']
                    if isinstance(network_scan, dict):
                        network_scan['open_ports'] = normalized['open_ports']
                        analysis['network_scan'] = network_scan
                except:
                    pass
            
            # Parser les autres champs JSON
            json_fields = ['sql_injection', 'xss_vulnerabilities', 'csrf_vulnerabilities',
                          'authentication_issues', 'authorization_issues', 'sensitive_data_exposure',
                          'ssl_tls_analysis', 'waf_detection', 'api_security', 'pentest_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_pentest_analysis_by_url(self, url):
        """Récupère une analyse Pentest par son URL avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ap.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_pentest ap
            LEFT JOIN entreprises e ON ap.entreprise_id = e.id
            WHERE ap.url = ?
            ORDER BY ap.date_analyse DESC
            LIMIT 1
        ''', (url,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_pentest_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Ajouter les ports ouverts au network_scan si présent
            if 'network_scan' in analysis and analysis['network_scan']:
                try:
                    network_scan = json.loads(analysis['network_scan']) if isinstance(analysis['network_scan'], str) else analysis['network_scan']
                    if isinstance(network_scan, dict):
                        network_scan['open_ports'] = normalized['open_ports']
                        analysis['network_scan'] = network_scan
                except:
                    pass
            
            # Parser les autres champs JSON
            json_fields = ['sql_injection', 'xss_vulnerabilities', 'csrf_vulnerabilities',
                         'authentication_issues', 'authorization_issues', 'sensitive_data_exposure',
                          'ssl_tls_analysis', 'waf_detection', 'api_security', 'pentest_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_pentest_analysis(self, analysis_id):
        """Récupère une analyse Pentest par ID avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ap.*, e.nom as entreprise_nom, e.id as entreprise_id
            FROM analyses_pentest ap
            LEFT JOIN entreprises e ON ap.entreprise_id = e.id
            WHERE ap.id = ?
        ''', (analysis_id,))
        
        row = cursor.fetchone()
        
        if row:
            analysis = dict(row)
            
            # Charger les données normalisées
            normalized = self._load_pentest_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Ajouter les ports ouverts au network_scan si présent
            if 'network_scan' in analysis and analysis['network_scan']:
                try:
                    network_scan = json.loads(analysis['network_scan']) if isinstance(analysis['network_scan'], str) else analysis['network_scan']
                    if isinstance(network_scan, dict):
                        network_scan['open_ports'] = normalized['open_ports']
                        analysis['network_scan'] = network_scan
                except:
                    pass
            
            # Parser les autres champs JSON
            json_fields = ['sql_injection', 'xss_vulnerabilities', 'csrf_vulnerabilities',
                          'authentication_issues', 'authorization_issues', 'sensitive_data_exposure',
                          'ssl_tls_analysis', 'waf_detection', 'api_security', 'pentest_details']
            for field in json_fields:
                if analysis.get(field):
                    try:
                        analysis[field] = json.loads(analysis[field])
                    except:
                        pass
            
            conn.close()
            return analysis
        
        conn.close()
        return None
    

    def get_all_pentest_analyses(self):
        """Récupère toutes les analyses Pentest avec données normalisées"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ap.*, e.nom as entreprise_nom
            FROM analyses_pentest ap
            LEFT JOIN entreprises e ON ap.entreprise_id = e.id
            ORDER BY ap.date_analyse DESC
        ''')
        
        rows = cursor.fetchall()
        
        analyses = []
        for row in rows:
            analysis = dict(row)
            analysis_id = analysis['id']
            
            # Charger les données normalisées
            normalized = self._load_pentest_analysis_normalized_data(cursor, analysis_id)
            analysis.update(normalized)
            
            # Ajouter le compteur pour compatibilité
            analysis['vulnerabilities_count'] = len(analysis.get('vulnerabilities', []))
            
            analyses.append(analysis)
        
        conn.close()
        return analyses
    

    def delete_pentest_analysis(self, analysis_id):
        """Supprime une analyse Pentest"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analyses_pentest WHERE id = ?', (analysis_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    

    def _load_pentest_analysis_normalized_data(self, cursor, analysis_id):
        """Charge les données normalisées d'une analyse Pentest"""
        # Charger les vulnérabilités
        cursor.execute('''
            SELECT name, severity, description, recommendation 
            FROM analysis_pentest_vulnerabilities 
            WHERE analysis_id = ?
        ''', (analysis_id,))
        vulnerabilities = []
        for row in cursor.fetchall():
            vuln = {'name': row['name']}
            if row['severity']:
                vuln['severity'] = row['severity']
            if row['description']:
                vuln['description'] = row['description']
            if row['recommendation']:
                vuln['recommendation'] = row['recommendation']
            vulnerabilities.append(vuln)
        
        # Charger les headers de sécurité
        cursor.execute('SELECT header_name, status FROM analysis_pentest_security_headers WHERE analysis_id = ?', (analysis_id,))
        security_headers = {}
        for row in cursor.fetchall():
            security_headers[row['header_name']] = {'status': row['status']}
        
        # Charger les vulnérabilités CMS
        cursor.execute('''
            SELECT name, severity, description 
            FROM analysis_pentest_cms_vulnerabilities 
            WHERE analysis_id = ?
        ''', (analysis_id,))
        cms_vulnerabilities = {}
        for row in cursor.fetchall():
            cms_vulnerabilities[row['name']] = {
                'severity': row['severity'],
                'description': row['description']
            }
        
        # Charger les ports ouverts
        cursor.execute('SELECT port, service FROM analysis_pentest_open_ports WHERE analysis_id = ?', (analysis_id,))
        open_ports = []
        for row in cursor.fetchall():
            port_data = {'port': row['port']}
            if row['service']:
                port_data['service'] = row['service']
            open_ports.append(port_data)
        
        return {
            'vulnerabilities': vulnerabilities,
            'security_headers': security_headers,
            'security_headers_analysis': security_headers,  # Compatibilité
            'cms_vulnerabilities': cms_vulnerabilities,
            'open_ports': open_ports
        }
    
