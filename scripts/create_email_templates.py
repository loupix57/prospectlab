"""
Script pour créer les modèles HTML d'emails de prospection
Charte graphique basée sur danielcraft.fr
"""

import json
from pathlib import Path
from datetime import datetime

# Couleurs de la charte graphique
COLOR_PRIMARY = "#E53935"  # Rouge
COLOR_BG = "#F8F8F8"  # Fond clair
COLOR_WHITE = "#FFFFFF"  # Blanc
COLOR_TEXT_DARK = "#333333"  # Texte foncé
COLOR_TEXT_MEDIUM = "#666666"  # Texte moyen

def create_html_template_1():
    """Modèle 1 : Modernisation technique"""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modernisation de votre site web</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {COLOR_BG};">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: {COLOR_BG};">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {COLOR_WHITE}; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 30px; background-color: {COLOR_PRIMARY}; border-radius: 8px 8px 0 0; text-align: center;">
                            <h1 style="margin: 0; color: {COLOR_WHITE}; font-size: 28px; font-weight: 600;">Modernisation de votre site web</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Bonjour {{nom}},
                            </p>
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                J'ai analysé le site web de <strong style="color: {COLOR_PRIMARY};">{{entreprise}}</strong> et j'ai identifié plusieurs opportunités d'amélioration pour moderniser votre présence digitale.
                            </p>
                            {{#if framework}}
                            <div style="background-color: {COLOR_BG}; padding: 20px; border-radius: 6px; margin: 25px 0;">
                                <h3 style="margin: 0 0 15px 0; color: {COLOR_PRIMARY}; font-size: 18px;">Observations techniques</h3>
                                <ul style="margin: 0; padding-left: 20px; color: {COLOR_TEXT_MEDIUM}; font-size: 15px; line-height: 1.8;">
                                    {{#if framework}}<li>Framework détecté : <strong>{{framework}}</strong></li>{{#endif}}
                                    {{#if cms}}<li>CMS utilisé : <strong>{{cms}}</strong></li>{{#endif}}
                                    {{#if hosting_provider}}<li>Hébergeur : <strong>{{hosting_provider}}</strong></li>{{#endif}}
                                    {{#if performance_score}}<li>Score de performance : <strong>{{performance_score}}/100</strong></li>{{#endif}}
                                </ul>
                            </div>
                            {{#endif}}
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                En tant que développeur web freelance spécialisé en TypeScript, React et Node.js, je peux vous accompagner pour :
                            </p>
                            <ul style="margin: 0 0 25px 0; padding-left: 20px; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.8;">
                                <li style="margin-bottom: 10px;"><strong style="color: {COLOR_PRIMARY};">Moderniser votre stack technique</strong> avec des technologies performantes et maintenables</li>
                                <li style="margin-bottom: 10px;"><strong style="color: {COLOR_PRIMARY};">Améliorer les performances</strong> (vitesse de chargement, expérience utilisateur)</li>
                                <li style="margin-bottom: 10px;"><strong style="color: {COLOR_PRIMARY};">Optimiser pour mobile</strong> avec un design responsive moderne</li>
                                <li style="margin-bottom: 10px;"><strong style="color: {COLOR_PRIMARY};">Renforcer la sécurité</strong> et la conformité aux standards</li>
                            </ul>
                            <div style="background-color: {COLOR_PRIMARY}; padding: 20px; border-radius: 6px; text-align: center; margin: 30px 0;">
                                <p style="margin: 0 0 15px 0; color: {COLOR_WHITE}; font-size: 18px; font-weight: 600;">Je propose un audit gratuit</p>
                                <p style="margin: 0; color: {COLOR_WHITE}; font-size: 14px;">Pour identifier les opportunités d'amélioration spécifiques à votre site</p>
                            </div>
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Seriez-vous disponible pour un échange de 15 minutes cette semaine pour discuter de vos besoins ?
                            </p>
                            <p style="margin: 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Cordialement,<br>
                                <strong style="color: {COLOR_PRIMARY};">Loïc DANIEL</strong><br>
                                Développeur web freelance<br>
                                <a href="https://danielcraft.fr" style="color: {COLOR_PRIMARY}; text-decoration: none;">danielcraft.fr</a>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 30px; background-color: {COLOR_BG}; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 12px;">
                                Vous recevez cet email car votre entreprise a été identifiée comme potentiellement intéressée par nos services de développement web.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def create_html_template_2():
    """Modèle 2 : Optimisation performance"""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Optimisation de performance</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {COLOR_BG};">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: {COLOR_BG};">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: {COLOR_WHITE}; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 30px; background-color: {COLOR_PRIMARY}; border-radius: 8px 8px 0 0; text-align: center;">
                            <h1 style="margin: 0; color: {COLOR_WHITE}; font-size: 28px; font-weight: 600;">Optimiser les performances de votre site</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Bonjour {{nom}},
                            </p>
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                La performance de votre site web <strong style="color: {COLOR_PRIMARY};">{{entreprise}}</strong> a un impact direct sur l'expérience de vos visiteurs et votre positionnement dans les moteurs de recherche.
                            </p>
                            {{#if performance_score}}
                            <div style="background-color: {COLOR_BG}; padding: 20px; border-radius: 6px; margin: 25px 0; border-left: 4px solid {COLOR_PRIMARY};">
                                <h3 style="margin: 0 0 10px 0; color: {COLOR_PRIMARY}; font-size: 18px;">Score de performance actuel</h3>
                                <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 15px;">
                                    Votre site obtient un score de <strong style="color: {COLOR_TEXT_DARK};">{{performance_score}}/100</strong>. 
                                    Une optimisation pourrait améliorer significativement ce score et l'expérience utilisateur.
                                </p>
                            </div>
                            {{#endif}}
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                <strong style="color: {COLOR_PRIMARY};">Les bénéfices concrets d'une optimisation :</strong>
                            </p>
                            <div style="margin: 25px 0;">
                                <div style="display: table; width: 100%; margin-bottom: 15px;">
                                    <div style="display: table-cell; width: 50px; vertical-align: top;">
                                        <div style="width: 40px; height: 40px; background-color: {COLOR_PRIMARY}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {COLOR_WHITE}; font-size: 20px; font-weight: bold;">⚡</div>
                                    </div>
                                    <div style="display: table-cell; vertical-align: top; padding-left: 15px;">
                                        <h4 style="margin: 0 0 5px 0; color: {COLOR_TEXT_DARK}; font-size: 16px;">Vitesse de chargement améliorée</h4>
                                        <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 14px;">Réduction de 40 à 60% du temps de chargement</p>
                                    </div>
                                </div>
                                <div style="display: table; width: 100%; margin-bottom: 15px;">
                                    <div style="display: table-cell; width: 50px; vertical-align: top;">
                                        <div style="width: 40px; height: 40px; background-color: {COLOR_PRIMARY}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {COLOR_WHITE}; font-size: 20px; font-weight: bold;">📱</div>
                                    </div>
                                    <div style="display: table-cell; vertical-align: top; padding-left: 15px;">
                                        <h4 style="margin: 0 0 5px 0; color: {COLOR_TEXT_DARK}; font-size: 16px;">Meilleure expérience mobile</h4>
                                        <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 14px;">Optimisation pour tous les appareils</p>
                                    </div>
                                </div>
                                <div style="display: table; width: 100%; margin-bottom: 15px;">
                                    <div style="display: table-cell; width: 50px; vertical-align: top;">
                                        <div style="width: 40px; height: 40px; background-color: {COLOR_PRIMARY}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {COLOR_WHITE}; font-size: 20px; font-weight: bold;">🔍</div>
                                    </div>
                                    <div style="display: table-cell; vertical-align: top; padding-left: 15px;">
                                        <h4 style="margin: 0 0 5px 0; color: {COLOR_TEXT_DARK}; font-size: 16px;">Amélioration du référencement</h4>
                                        <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 14px;">Meilleur positionnement dans Google</p>
                                    </div>
                                </div>
                            </div>
                            <div style="background-color: {COLOR_PRIMARY}; padding: 20px; border-radius: 6px; text-align: center; margin: 30px 0;">
                                <p style="margin: 0 0 10px 0; color: {COLOR_WHITE}; font-size: 18px; font-weight: 600;">Audit & Optimisation - 800€</p>
                                <p style="margin: 0; color: {COLOR_WHITE}; font-size: 14px;">Audit complet + correctifs prioritaires + métriques avant/après</p>
                            </div>
                            <p style="margin: 0 0 20px 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Je propose un audit gratuit pour identifier les points d'amélioration prioritaires de votre site.
                            </p>
                            <p style="margin: 0; color: {COLOR_TEXT_DARK}; font-size: 16px; line-height: 1.6;">
                                Cordialement,<br>
                                <strong style="color: {COLOR_PRIMARY};">Loïc DANIEL</strong><br>
                                Développeur web freelance<br>
                                <a href="https://danielcraft.fr" style="color: {COLOR_PRIMARY}; text-decoration: none;">danielcraft.fr</a>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 30px; background-color: {COLOR_BG}; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: {COLOR_TEXT_MEDIUM}; font-size: 12px;">
                                Vous recevez cet email car votre entreprise a été identifiée comme potentiellement intéressée par nos services de développement web.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

# Suite dans le prochain message car c'est trop long...

if __name__ == "__main__":
    print("Génération des modèles HTML...")
    # Les modèles seront créés directement dans le JSON
    print("OK")

