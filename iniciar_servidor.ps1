# ============================================
# ToolKinventario - Iniciar Servidor
# Inicia el servidor de forma oculta y abre el navegador
# ============================================

$ErrorActionPreference = "SilentlyContinue"

$port = 5050

# Detener cualquier instancia anterior del servidor
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connection) {
    $processId = $connection.OwningProcess
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Buscar directorio del proyecto
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

# Buscar run.py
$runPyPath = Join-Path $scriptDir "run.py"
if (-not (Test-Path $runPyPath)) {
    $runPyPath = Join-Path $scriptDir "..\run.py"
}

if (-not (Test-Path $runPyPath)) {
    exit 1
}

# Configurar para ocultar ventana
$startupinfo = New-Object System.Diagnostics.ProcessStartInfo
$startupinfo.FileName = "python"
$startupinfo.Arguments = "`"$runPyPath`""
$startupinfo.WorkingDirectory = $scriptDir
$startupinfo.UseShellExecute = $false
$startupinfo.CreateNoWindow = $true
$startupinfo.RedirectStandardOutput = $false
$startupinfo.RedirectStandardError = $false

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $startupinfo

try {
    $process.Start() | Out-Null
} catch {
    exit 1
}

# Esperar a que el servidor este listo
$maxWait = 20
$waited = 0
$serverReady = $false

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn -and $conn.State -eq "Listen") {
        $serverReady = $true
        break
    }
    
    # Verificar si el proceso sigue activo
    if ($process.HasExited) {
        break
    }
    
    $waited++
}

if (-not $serverReady) {
    exit 1
}

# Abrir navegador
Start-Process -FilePath "http://127.0.0.1:$port"

exit 0
