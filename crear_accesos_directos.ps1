# ============================================
# ToolKinventario - Crear Accesos Directos
# Crea iconos en Escritorio y Menu Inicio
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ToolKinventario - Crear Accesos Directos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SUCCESS = "Green"
$ERRORCOLOR = "Red"

# Buscar iniciar_servidor.ps1
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$launcherPath = $null
$possiblePaths = @(
    "$scriptDir\iniciar_servidor.ps1",
    "$scriptDir\..\iniciar_servidor.ps1"
)

foreach ($path in $possiblePaths) {
    $resolvedPath = Resolve-Path $path -ErrorAction SilentlyContinue
    if ($resolvedPath -and (Test-Path $resolvedPath)) {
        $launcherPath = $resolvedPath
        break
    }
}

if (-not $launcherPath) {
    Write-Host "[X] No se encontro iniciar_servidor.ps1" -ForegroundColor $ERRORCOLOR
    Write-Host "    Busque en:" -ForegroundColor Yellow
    foreach ($path in $possiblePaths) {
        Write-Host "    - $path" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "[OK] Script encontrado: $launcherPath" -ForegroundColor $SUCCESS

# Obtener rutas
$desktopPath = [Environment]::GetFolderPath("Desktop")
$startMenuPath = [Environment]::GetFolderPath("StartMenu")
$programsPath = Join-Path $startMenuPath "Programs"
$appFolderPath = Join-Path $programsPath "ToolKinventario"

# Icono
$iconPath = $null
$iconPaths = @(
    "$scriptDir\static\icon.ico",
    "$scriptDir\icon.ico"
)

foreach ($path in $iconPaths) {
    if (Test-Path $path) {
        $iconPath = $path
        break
    }
}

Write-Host ""

# Funcion para crear acceso directo
function New-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$WorkingDir,
        [string]$Description,
        [string]$IconPath
    )
    
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$TargetPath`""
        $Shortcut.WorkingDirectory = $WorkingDir
        $Shortcut.Description = $Description
        
        if ($IconPath -and (Test-Path $IconPath)) {
            $Shortcut.IconLocation = $IconPath
        }
        
        $Shortcut.Save()
        return $true
    } catch {
        Write-Host "[X] Error creando acceso directo: $_" -ForegroundColor $ERRORCOLOR
        return $false
    }
}

# Crear carpeta en Menu Inicio
Write-Host "Creando carpeta Menu Inicio..." -ForegroundColor Cyan
if (-not (Test-Path $appFolderPath)) {
    New-Item -ItemType Directory -Path $appFolderPath -Force | Out-Null
}

# Crear acceso directo en Escritorio
Write-Host ""
Write-Host "Creando acceso directo en Escritorio..." -ForegroundColor Cyan
$desktopShortcut = Join-Path $desktopPath "ToolKinventario.lnk"
$workingDir = Split-Path $launcherPath -Parent

$result = New-Shortcut -ShortcutPath $desktopShortcut -TargetPath $launcherPath -WorkingDir $workingDir -Description "ToolKinventario - Sistema de Gestion de Inventario" -IconPath $iconPath

if ($result) {
    Write-Host "[OK] Acceso directo en Escritorio: ToolKinventario.lnk" -ForegroundColor $SUCCESS
} else {
    Write-Host "[X] Error en Escritorio" -ForegroundColor $ERRORCOLOR
}

# Crear acceso directo en Menu Inicio
Write-Host ""
Write-Host "Creando acceso directo en Menu Inicio..." -ForegroundColor Cyan

$startShortcut = Join-Path $appFolderPath "ToolKinventario.lnk"
$result = New-Shortcut -ShortcutPath $startShortcut -TargetPath $launcherPath -WorkingDir $workingDir -Description "ToolKinventario - Sistema de Gestion de Inventario" -IconPath $iconPath

if ($result) {
    Write-Host "[OK] Acceso directo en Menu Inicio: ToolKinventario.lnk" -ForegroundColor $SUCCESS
} else {
    Write-Host "[X] Error en Menu Inicio" -ForegroundColor $ERRORCOLOR
}

# Preguntar por inicio automatico
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ACCESOS DIRECTOS CREADOS" -ForegroundColor $SUCCESS
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Escritorio: ToolKinventario.lnk" -ForegroundColor White
Write-Host "Menu Inicio: ToolKinventario.lnk" -ForegroundColor White
Write-Host ""

$autoStart = Read-Host "[?] Agregar al inicio automatico de Windows? (S/N)"

if ($autoStart -eq "S" -or $autoStart -eq "s") {
    Write-Host ""
    Write-Host "Agregando al inicio automatico..." -ForegroundColor Cyan
    
    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    $regKey = "ToolKinventario"
    
    try {
        Set-ItemProperty -Path $regPath -Name $regKey -Value "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$launcherPath`""
        Write-Host "[OK] Agregado al inicio automatico" -ForegroundColor $SUCCESS
    } catch {
        Write-Host "[X] Error agregando al inicio: $_" -ForegroundColor $ERRORCOLOR
    }
}

Write-Host ""
Write-Host "Listo! Puede ejecutar ToolKinventario desde el Escritorio." -ForegroundColor $SUCCESS
Write-Host ""
