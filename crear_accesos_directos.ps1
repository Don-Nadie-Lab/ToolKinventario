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

# Buscar ejecutables
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Buscar ToolKinventarioLauncher.exe
$launcherPath = $null
$possiblePaths = @(
    "$scriptDir\ToolKinventarioLauncher.exe",
    "$scriptDir\dist\ToolKinventario\ToolKinventarioLauncher.exe",
    "$scriptDir\..\dist\ToolKinventario\ToolKinventarioLauncher.exe",
    "$scriptDir\..\ToolKinventario-Portable\ToolKinventarioLauncher.exe"
)

foreach ($path in $possiblePaths) {
    $resolvedPath = Resolve-Path $path -ErrorAction SilentlyContinue
    if ($resolvedPath -and (Test-Path $resolvedPath)) {
        $launcherPath = $resolvedPath
        break
    }
}

if (-not $launcherPath) {
    Write-Host "[X] No se encontro ToolKinventarioLauncher.exe" -ForegroundColor $ERROR
    Write-Host "    Busque en:" -ForegroundColor Yellow
    foreach ($path in $possiblePaths) {
        Write-Host "    - $path" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "[OK] Ejecutable encontrado: $launcherPath" -ForegroundColor $SUCCESS

# Obtener rutas
$desktopPath = [Environment]::GetFolderPath("Desktop")
$startMenuPath = [Environment]::GetFolderPath("StartMenu")
$programsPath = Join-Path $startMenuPath "Programs"
$appFolderPath = Join-Path $programsPath "ToolKinventario"

# Icono
$iconPath = $null
$iconPaths = @(
    "$scriptDir\static\icon.ico",
    "$scriptDir\icon.ico",
    (Split-Path $launcherPath -Parent) + "\static\icon.ico"
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
        $Shortcut.TargetPath = $TargetPath
        $Shortcut.WorkingDirectory = $WorkingDir
        $Shortcut.Description = $Description
        
        if ($IconPath -and (Test-Path $IconPath)) {
            $Shortcut.IconLocation = $IconPath
        }
        
        $Shortcut.Save()
        return $true
    } catch {
        Write-Host "[X] Error creando acceso directo: $_" -ForegroundColor $ERROR
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
    Write-Host "[X] Error en Escritorio" -ForegroundColor $ERROR
}

# Crear acceso directo en Menu Inicio
Write-Host ""
Write-Host "Creando acceso directo en Menu Inicio..." -ForegroundColor Cyan

$startShortcut = Join-Path $appFolderPath "ToolKinventario.lnk"
$result = New-Shortcut -ShortcutPath $startShortcut -TargetPath $launcherPath -WorkingDir $workingDir -Description "ToolKinventario - Sistema de Gestion de Inventario" -IconPath $iconPath

if ($result) {
    Write-Host "[OK] Acceso directo en Menu Inicio: ToolKinventario.lnk" -ForegroundColor $SUCCESS
} else {
    Write-Host "[X] Error en Menu Inicio" -ForegroundColor $ERROR
}

# Crear acceso directo para Desinstalar
Write-Host ""
Write-Host "Creando acceso directo de Desinstalacion..." -ForegroundColor Cyan

$uninstallExe = (Split-Path $launcherPath -Parent) + "\unins000.exe"
if (Test-Path $uninstallExe) {
    $uninstallShortcut = Join-Path $appFolderPath "Desinstalar ToolKinventario.lnk"
    $result = New-Shortcut -ShortcutPath $uninstallShortcut -TargetPath $uninstallExe -WorkingDir (Split-Path $uninstallExe -Parent) -Description "Desinstalar ToolKinventario"
    
    if ($result) {
        Write-Host "[OK] Acceso directo de Desinstalacion creado" -ForegroundColor $SUCCESS
    }
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
        Set-ItemProperty -Path $regPath -Name $regKey -Value "`"$launcherPath`""
        Write-Host "[OK] Agregado al inicio automatico" -ForegroundColor $SUCCESS
    } catch {
        Write-Host "[X] Error agregando al inicio: $_" -ForegroundColor $ERROR
    }
}

Write-Host ""
Write-Host "Listo! Puede ejecutar ToolKinventario desde el Escritorio." -ForegroundColor $SUCCESS
Write-Host ""
