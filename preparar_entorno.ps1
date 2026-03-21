# ============================================
# ToolKinventario - Preparar Entorno
# Instala Python y dependencias en Windows limpio
# ============================================

param(
    [string]$InstalarPython = "S",
    [string]$PythonVersion = "3.11.8"
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ToolKinventario - Preparar Entorno" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Colores
$SUCCESS = "Green"
$ERRORCOLOR = "Red"
$WARNING = "Yellow"

function Write-Step {
    param([string]$Message)
    Write-Host "[...] $Message" -ForegroundColor White
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor $SUCCESS
}

function Write-Err {
    param([string]$Message)
    Write-Host "[X] $Message" -ForegroundColor $ERRORCOLOR
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor $WARNING
}

# Verificar si es administrador
function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ============================================
# Paso 1: Verificar Python
# ============================================
Write-Host ""
Write-Host "Paso 1: Verificando Python..." -ForegroundColor Magenta

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if ($pythonCmd) {
    $pythonVersion = & python --version 2>&1
    Write-Success "Python encontrado: $pythonVersion"
    $pythonPath = $pythonCmd.Source
    $pythonDir = Split-Path $pythonPath -Parent
    Write-Host "    Ubicacion: $pythonDir"
} else {
    Write-Warn "Python NO encontrado"
    
    if ($InstalarPython -eq "S") {
        Write-Host ""
        Write-Host "Instalando Python $PythonVersion..." -ForegroundColor Cyan
        
        $localInstaller = Join-Path $PSScriptRoot "python-installer.exe"
        $installerPath = "$env:TEMP\python-$PythonVersion-amd64.exe"
        
        if (Test-Path $localInstaller) {
            Write-Step "Usando instalador local..."
            Copy-Item -Path $localInstaller -Destination $installerPath -Force
            Write-Success "Instalador local encontrado"
        } else {
            Write-Step "Buscando instalador local..."
            Write-Warn "No se encontro python-installer.exe en la carpeta del proyecto"
            Write-Host "Descargando Python $PythonVersion..." -ForegroundColor Cyan
            
            $pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
            
            try {
                Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
                Write-Success "Descarga completada"
            } catch {
                Write-Err "Error descargando Python: $_"
                Write-Host "Descargue Python manualmente desde: https://www.python.org/downloads/" -ForegroundColor Yellow
                exit 1
            }
        }
        
        Write-Host ""
        Write-Host "Instalando Python (esto puede tomar varios minutos)..." -ForegroundColor Yellow
        Write-Host ""
        
        try {
            Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
            
            Write-Step "Verificando instalacion..."
            Start-Sleep -Seconds 5
            
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            if ($pythonCmd) {
                Write-Success "Python instalado correctamente"
            } else {
                Write-Err "Python no se pudo instalar automaticamente"
                Write-Host "Por favor instale Python manualmente desde: https://www.python.org/downloads/" -ForegroundColor Yellow
            }
        } catch {
            Write-Err "Error instalando Python: $_"
            Write-Host "Por favor instale Python manualmente desde: https://www.python.org/downloads/" -ForegroundColor Yellow
        }
    } else {
        Write-Err "Python es requerido para continuar"
        exit 1
    }
}

# ============================================
# Paso 2: Instalar dependencias
# ============================================
Write-Host ""
Write-Host "Paso 2: Instalando dependencias..." -ForegroundColor Magenta

# Crear carpeta del proyecto si no existe
$projectDir = $PSScriptRoot
$requirementsFile = Join-Path $projectDir "requirements.txt"

if (-not (Test-Path $requirementsFile)) {
    Write-Err "No se encontro requirements.txt"
    exit 1
}

# Verificar pip
Write-Step "Verificando pip..."
$pipCmd = Get-Command pip -ErrorAction SilentlyContinue
if (-not $pipCmd) {
    Write-Step "Instalando pip..."
    python -m ensurepip --upgrade 2>$null
}

# Actualizar pip
Write-Step "Actualizando pip..."
python -m pip install --upgrade pip 2>$null | Out-Null

# Instalar dependencias
Write-Host ""
Write-Step "Instalando dependencias de requirements.txt..."

try {
    pip install -r $requirementsFile --quiet
    Write-Success "Dependencias instaladas correctamente"
} catch {
    Write-Err "Error instalando dependencias: $_"
    exit 1
}

# ============================================
# Paso 3: Crear estructura de carpetas
# ============================================
Write-Host ""
Write-Host "Paso 3: Creando estructura de carpetas..." -ForegroundColor Magenta

$carpetas = @("database", "backups", "logs", "uploads")
foreach ($carpeta in $carpetas) {
    $carpetaPath = Join-Path $projectDir $carpeta
    if (-not (Test-Path $carpetaPath)) {
        New-Item -ItemType Directory -Path $carpetaPath -Force | Out-Null
        Write-Success "Carpeta creada: $carpeta"
    } else {
        Write-Success "Carpeta existente: $carpeta"
    }
}

# ============================================
# Finalizacion
# ============================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ENTORNO PREPARADO" -ForegroundColor $SUCCESS
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar la aplicacion:" -ForegroundColor White
Write-Host "  python run.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "O usar el lanzador:" -ForegroundColor White
Write-Host "  python installer/lanzador_optimizado.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Usuario por defecto: admin" -ForegroundColor White
Write-Host "Contrasena por defecto: admin123" -ForegroundColor White
Write-Host ""
