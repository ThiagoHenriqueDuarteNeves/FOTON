@echo off
cd /d "%~dp0"
echo Iniciando Electron de: %CD%
"%~dp0node_modules\electron\dist\electron.exe" . --no-sandbox
