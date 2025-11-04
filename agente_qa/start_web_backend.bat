@echo off
echo ========================================
echo  Iniciando Agente QA - Web Interface
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo [2/3] Instalando dependencias do backend...
cd backend
pip install -r requirements.txt

echo [3/3] Iniciando servidor FastAPI...
echo.
echo ========================================
echo  BACKEND RODANDO
echo ========================================
echo  API: http://localhost:8000
echo  Docs: http://localhost:8000/docs
echo ========================================
echo.
python api.py
