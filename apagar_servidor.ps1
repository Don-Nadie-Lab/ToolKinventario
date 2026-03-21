# ============================================
# ToolKinventario - Apagar Servidor
# Detiene el servidor de forma oculta
# ============================================

$ErrorActionPreference = "SilentlyContinue"
$port = 5050

# Detener procesos en el puerto
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    $processId = $connection.OwningProcess
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
}

# Detener cualquier proceso python relacionado
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*ToolKinventario*" -or
    $_.MainWindowTitle -like "*run.py*" -or
    $_.MainWindowTitle -like "*Flask*"
}

foreach ($proc in $pythonProcesses) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}

exit 0
