# ============================================
# ToolKinventario - Iniciar Servidor
# Inicia el servidor de forma oculta y abre el navegador
# ============================================

$ErrorActionPreference = "SilentlyContinue"

# Detener cualquier instancia anterior del servidor
$port = 5050
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

# Iniciar servidor OCULTO (sin ventana)
$pythonPath = "python"
$process = Start-Process -FilePath $pythonPath -ArgumentList $runPyPath -PassThru -WindowStyle Hidden

if (-not $process) {
    exit 1
}

# Esperar a que el servidor este listo
$maxWait = 15
$waited = 0

while ($waited -lt $maxWait) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn -and $conn.State -eq "Listen") {
        break
    }
    Start-Sleep -Seconds 1
    $waited++
}

# Abrir navegador (esto muestra una ventana pero es intencional)
Start-Process -FilePath "http://127.0.0.1:$port"

exit 0
