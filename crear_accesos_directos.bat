@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "crear_accesos_directos.ps1"
pause
