@echo off
echo ========================================
echo  Agente QA - Backend FastAPI
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Ativando ambiente virtual...
call ..\.venv\Scripts\activate.bat

echo [2/3] Instalando dependencias do backend...
pip install -r requirements.txt

echo [3/3] Iniciando servidor FastAPI...
echo.
echo API rodando em: http://localhost:8000
echo Documentacao: http://localhost:8000/docs
echo.
python api.py

pause
