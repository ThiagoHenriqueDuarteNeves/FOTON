@echo off
SET "BASE_DIR=llm_agent_test"

:: Cria as pastas
mkdir %BASE_DIR%
mkdir %BASE_DIR%\agent

:: Cria os arquivos
cd %BASE_DIR%
echo.> main.py
echo.> requirements.txt

cd agent
echo.> __init__.py
echo.> browser.py
echo.> llm.py
echo.> utils.py

echo Estrutura criada com sucesso em %BASE_DIR%
pause
