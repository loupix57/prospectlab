# Script PowerShell pour nettoyer la base de données ProspectLab

param(
    [switch]$Clear,
    [switch]$NoConfirm,
    [switch]$Stats,
    [string[]]$Tables,
    [string]$DbPath
)

# Gérer aussi les arguments Unix-style (--clear, --no-confirm, etc.)
# pour compatibilité avec les habitudes de ligne de commande
$argsList = $args
foreach ($arg in $argsList) {
    if ($arg -eq "--clear" -or $arg -eq "-clear") {
        $Clear = $true
    }
    elseif ($arg -eq "--no-confirm" -or $arg -eq "-no-confirm") {
        $NoConfirm = $true
    }
    elseif ($arg -eq "--stats" -or $arg -eq "-stats") {
        $Stats = $true
    }
    elseif ($arg -eq "--db-path" -or $arg -eq "-db-path") {
        # Le prochain argument est la valeur
        $idx = [array]::IndexOf($argsList, $arg)
        if ($idx -ge 0 -and $idx -lt ($argsList.Length - 1)) {
            $DbPath = $argsList[$idx + 1]
        }
    }
    elseif ($arg -eq "--tables" -or $arg -eq "-tables") {
        # Les arguments suivants sont les noms de tables
        $idx = [array]::IndexOf($argsList, $arg)
        if ($idx -ge 0) {
            $Tables = @()
            for ($i = $idx + 1; $i -lt $argsList.Length; $i++) {
                if ($argsList[$i] -match "^--" -or $argsList[$i] -match "^-") {
                    break
                }
                $Tables += $argsList[$i]
            }
        }
    }
}

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
    
    if ($Tables -and $Tables.Count -gt 0) {
        $pythonArgs += "--tables"
        foreach ($table in $Tables) {
            $pythonArgs += $table
        }
    }
}

if ($DbPath -and $DbPath.Trim() -ne "") {
    $pythonArgs += "--db-path"
    $pythonArgs += $DbPath.Trim()
}

# Essayer d'utiliser conda si disponible, sinon python
$pythonExe = "python"
$useConda = $false
$condaEnv = "prospectlab"

try {
    $condaCheck = conda env list 2>$null
    if ($condaCheck -match $condaEnv) {
        Write-Host "Utilisation de l'environnement Conda: $condaEnv" -ForegroundColor Cyan
        $useConda = $true
        
        # Trouver le chemin Python dans l'environnement conda
        $condaInfo = conda info --envs 2>$null
        $envLine = $condaInfo | Select-String $condaEnv
        if ($envLine) {
            $envPath = ($envLine -split '\s+')[1]
            if ($envPath) {
                $condaPython = Join-Path $envPath "python.exe"
                if (Test-Path $condaPython) {
                    $pythonExe = $condaPython
                }
            }
        }
    }
} catch {
    # Si conda n'est pas disponible, utiliser python directement
}

# Exécuter le script Python dans le terminal actuel
Write-Host "Exécution du script de nettoyage de la base de données..." -ForegroundColor Cyan
Write-Host ""

try {
    # Construire les arguments pour Python
    $allArgs = @()
    $allArgs += $pythonScript
    
    # Ajouter tous les arguments Python en s'assurant qu'ils sont bien formatés
    foreach ($arg in $pythonArgs) {
        if ($arg) {
            $argStr = $arg.ToString().Trim()
            if ($argStr -ne "") {
                $allArgs += $argStr
            }
        }
    }
    
    # Debug: afficher les arguments (commenté par défaut)
    # Write-Host "Arguments: $($allArgs -join ' ')" -ForegroundColor Gray
    
    # Exécuter avec & en passant les arguments correctement
    # Utiliser l'opérateur de call & directement
    & $pythonExe $allArgs
    
    # Vérifier le code de sortie
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        Write-Host "`nErreur lors de l'exécution du script Python (code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Erreur: $_" -ForegroundColor Red
    Write-Host "Commande: $pythonExe $($allArgs -join ' ')" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Terminé!" -ForegroundColor Green

