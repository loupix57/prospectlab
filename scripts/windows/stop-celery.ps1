# Script pour arrêter Celery proprement

Write-Host "Arrêt de Celery..." -ForegroundColor Yellow
Write-Host ""

# Fonction pour obtenir la ligne de commande d'un processus
function Get-ProcessCommandLine {
    param([int]$ProcessId)
    try {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId"
        return $process.CommandLine
    } catch {
        return $null
    }
}

# Trouver tous les processus Python
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
$celeryProcesses = @()

# Filtrer les processus qui exécutent Celery
foreach ($proc in $pythonProcesses) {
    $commandLine = Get-ProcessCommandLine -ProcessId $proc.Id
    if ($commandLine) {
        # Vérifier si c'est un processus Celery (worker, beat, ou run_celery.py)
        if ($commandLine -match "celery.*worker" -or 
            $commandLine -match "celery.*beat" -or 
            $commandLine -match "run_celery\.py" -or
            $commandLine -match "celery_app") {
            $celeryProcesses += $proc
        }
    }
}

if ($celeryProcesses.Count -gt 0) {
    Write-Host "Processus Celery trouvés: $($celeryProcesses.Count)" -ForegroundColor Cyan
    
    foreach ($proc in $celeryProcesses) {
        $commandLine = Get-ProcessCommandLine -ProcessId $proc.Id
        $procType = "inconnu"
        if ($commandLine -match "celery.*worker") { $procType = "worker" }
        elseif ($commandLine -match "celery.*beat") { $procType = "beat" }
        elseif ($commandLine -match "run_celery\.py") { $procType = "wrapper" }
        
        Write-Host "  - Arrêt du processus $($proc.Id) ($procType)..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Host "    ✓ Processus $($proc.Id) arrêté" -ForegroundColor Green
        } catch {
            Write-Host "    ✗ Erreur lors de l'arrêt du processus $($proc.Id): $_" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Celery arrêté." -ForegroundColor Green
} else {
    Write-Host "Aucun processus Celery trouvé." -ForegroundColor Yellow
}

