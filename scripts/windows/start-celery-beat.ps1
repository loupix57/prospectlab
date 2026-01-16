# Script pour démarrer Celery Beat (tâches périodiques)

Write-Host "Démarrage de Celery Beat..." -ForegroundColor Green
Write-Host ""

# Vérifier que nous sommes dans le bon répertoire
if (-not (Test-Path "celery_app.py")) {
    Write-Host "ERREUR: Ce script doit être exécuté depuis le répertoire du projet" -ForegroundColor Red
    Write-Host "Répertoire actuel: $PWD" -ForegroundColor Yellow
    exit 1
}

# Vérifier la configuration Redis
Write-Host "Vérification de la configuration Redis..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "CELERY_BROKER_URL=(.+)") {
        $brokerUrl = $matches[1].Trim()
        Write-Host "  BROKER_URL: $brokerUrl" -ForegroundColor Cyan
        
        # Extraire l'host et le port
        if ($brokerUrl -match "redis://([^:]+):(\d+)/(\d+)") {
            $redisHost = $matches[1]
            $redisPort = $matches[2]
            
            Write-Host "  Test de connexion Redis sur ${redisHost}:${redisPort}..." -ForegroundColor Yellow
            $connection = Test-NetConnection -ComputerName $redisHost -Port $redisPort -WarningAction SilentlyContinue
            
            if (-not $connection.TcpTestSucceeded) {
                Write-Host "  ✗ Redis n'est pas accessible!" -ForegroundColor Red
                Write-Host "  Vérifiez que Redis est démarré sur ${redisHost}:${redisPort}" -ForegroundColor Yellow
                exit 1
            } else {
                Write-Host "  ✓ Redis est accessible" -ForegroundColor Green
            }
        }
    }
}

Write-Host ""
Write-Host "Celery Beat va exécuter les tâches périodiques:" -ForegroundColor Yellow
Write-Host "  - Nettoyage des fichiers uploads/exports (toutes les heures)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur Ctrl+C pour arrêter Celery Beat" -ForegroundColor Cyan
Write-Host ""

# Activer l'environnement conda et lancer Celery Beat
$condaEnv = "prospectlab"

# Vérifier si conda est disponible
$condaPath = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaPath) {
    Write-Host "ERREUR: Conda n'est pas trouvé dans le PATH" -ForegroundColor Red
    Write-Host "Activez manuellement l'environnement conda puis lancez:" -ForegroundColor Yellow
    Write-Host "  celery -A celery_app beat --loglevel=info" -ForegroundColor Cyan
    exit 1
}

# Lancer Celery Beat
Write-Host "Lancement de Celery Beat..." -ForegroundColor Green
Write-Host "Note: Pour arrêter Celery Beat, utilisez Ctrl+C ou le script stop-celery-beat.ps1" -ForegroundColor Cyan
Write-Host ""

try {
    & conda run -n $condaEnv celery -A celery_app beat --loglevel=info
} catch {
    Write-Host "`nCelery Beat arrêté." -ForegroundColor Yellow
} finally {
    Write-Host "Nettoyage terminé." -ForegroundColor Green
}

