@echo off
echo ========================================
echo  Agente QA - Frontend React
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Instalando dependencias do frontend...
call npm install

echo [2/2] Iniciando servidor de desenvolvimento...
echo.
echo Frontend rodando em: http://localhost:3000
echo.
call npm run dev

pause
