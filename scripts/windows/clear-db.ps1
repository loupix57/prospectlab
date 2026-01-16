# Script PowerShell pour nettoyer la base de données ProspectLab

param(
    [switch]$Clear,
    [switch]$NoConfirm,
    [switch]$Stats,
    [string[]]$Tables,
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

# Déterminer le chemin du script Python
$scriptDir = Split-Path -Parent $PSScriptRoot
$pythonScript = Join-Path $scriptDir "clear_db.py"

# Convertir en chemin absolu pour éviter les problèmes
$pythonScript = (Resolve-Path $pythonScript -ErrorAction SilentlyContinue).Path
if (-not $pythonScript) {
    $pythonScript = Join-Path $scriptDir "clear_db.py"
}

# Vérifier que le script Python existe
if (-not (Test-Path $pythonScript)) {
    Write-Host "Erreur: Le script clear_db.py n'a pas été trouvé à: $pythonScript" -ForegroundColor Red
    exit 1
}

# Construire la commande Python
$pythonArgs = @()

if ($Stats) {
    $pythonArgs += "--stats"
}

if ($Clear) {
    $pythonArgs += "--clear"
    
    if ($NoConfirm) {
        $pythonArgs += "--no-confirm"
    }
    
    if ($Tables) {
        $pythonArgs += "--tables"
        $pythonArgs += $Tables
    }
}

if ($DbPath) {
    $pythonArgs += "--db-path"
    $pythonArgs += $DbPath
}

# Essayer d'utiliser conda si disponible, sinon python
$pythonExe = "python"
$useConda = $false
$condaEnv = "prospectlab"
$condaPythonPath = $null

try {
    $condaCheck = conda env list 2>$null
    if ($condaCheck -match $condaEnv) {
        Write-Host "Utilisation de l'environnement Conda: $condaEnv" -ForegroundColor Cyan
        
        # Essayer de trouver le chemin Python dans l'environnement conda
        $condaInfo = conda info --envs 2>$null
        $envLine = $condaInfo | Select-String $condaEnv
        if ($envLine) {
            $envPath = ($envLine -split '\s+')[1]
            if ($envPath) {
                $condaPythonPath = Join-Path $envPath "python.exe"
                if (Test-Path $condaPythonPath) {
                    $useConda = $true
                    $pythonExe = $condaPythonPath
                }
            }
        }
        
        # Si on n'a pas trouvé le chemin direct, utiliser conda run
        if (-not $useConda) {
            $useConda = $true
        }
    }
} catch {
    # Si conda n'est pas disponible, utiliser python directement
}

# Exécuter le script Python dans le terminal actuel
Write-Host "Exécution du script de nettoyage de la base de données..." -ForegroundColor Cyan
Write-Host ""

try {
    $exitCode = 0
    
    if ($useConda -and $condaPythonPath) {
        # Utiliser directement Python depuis l'environnement conda
        $allArgs = @($pythonScript) + $pythonArgs
        & $pythonExe $allArgs
        $exitCode = $LASTEXITCODE
    } elseif ($useConda) {
        # Utiliser conda run si on n'a pas trouvé le chemin direct
        $allArgs = @("run", "-n", $condaEnv, "--no-capture-output", "python", $pythonScript)
        $allArgs += $pythonArgs
        
        # Exécuter conda avec tous les arguments dans le terminal actuel
        & conda $allArgs
        $exitCode = $LASTEXITCODE
    } else {
        # Utiliser python directement avec le chemin complet
        $allArgs = @($pythonScript) + $pythonArgs
        & $pythonExe $allArgs
        $exitCode = $LASTEXITCODE
    }
    
    # Si exitCode est null, considérer que c'est un succès
    if ($exitCode -eq $null) {
        $exitCode = 0
    }
    
    if ($exitCode -ne 0) {
        Write-Host "`nErreur lors de l'exécution du script Python (code: $exitCode)" -ForegroundColor Red
        exit $exitCode
    }
} catch {
    Write-Host "Erreur: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Terminé!" -ForegroundColor Green

