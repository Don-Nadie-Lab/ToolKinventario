@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "iniciar_servidor.ps1"
