@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   INSTALACAO AGENTE QA DESKTOP
echo ========================================
echo.
echo Diretorio atual: %CD%
echo.

REM Verificar Node.js
echo [1/6] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo Por favor, instale Node.js de: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
echo [OK] Node.js instalado: !NODE_VER!

REM Verificar Python
echo.
echo [2/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python de: https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo [OK] Python instalado: !PY_VER!

REM Criar ambiente virtual
echo.
echo [3/6] Criando ambiente virtual Python...
echo Navegando para diretorio AgenteIA...
cd ..\
echo Diretorio atual: %CD%

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)

REM Ativar ambiente e instalar dependências Python
echo.
echo [4/6] Instalando dependencias Python...
echo Ativando ambiente virtual...
if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado em: %CD%\.venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo Atualizando pip...
python -m pip install --upgrade pip --quiet

if exist "requirements.txt" (
    echo Instalando dependencias de requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias Python
        pause
        exit /b 1
    )
) else (
    echo [AVISO] requirements.txt nao encontrado em: %CD%
    echo Instalando pacotes basicos...
    pip install playwright python-dotenv openai anthropic google-generativeai
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar pacotes basicos
        pause
        exit /b 1
    )
)
echo [OK] Dependencias Python instaladas

REM Instalar Playwright browsers
echo.
echo [5/6] Instalando Playwright Chromium...
echo (Isso pode demorar alguns minutos...)
playwright install chromium
if errorlevel 1 (
    echo [AVISO] Falha ao instalar Playwright, mas continuando...
) else (
    echo [OK] Playwright browsers instalados
)

REM Instalar dependências Node.js
echo.
echo [6/6] Instalando dependencias Node.js e fazendo build...
echo Navegando para frontend...
cd agente_qa\frontend
echo Diretorio atual: %CD%

if not exist "package.json" (
    echo [ERRO] package.json nao encontrado em: %CD%
    pause
    exit /b 1
)

echo Instalando dependencias Node.js...
call npm install
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias Node.js
    echo Tentando limpar cache...
    call npm cache clean --force
    call npm install
    if errorlevel 1 (
        pause
        exit /b 1
    )
)
echo [OK] Dependencias Node.js instaladas

REM Build da aplicação
echo.
echo Fazendo build da aplicacao React...
call npm run build
if errorlevel 1 (
    echo [ERRO] Falha ao fazer build
    pause
    exit /b 1
)
echo [OK] Build concluido

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Para iniciar a aplicacao, execute:
echo   start-electron.bat
echo.
echo Ou navegue ate:
echo   %cd%
echo E execute: start-electron.bat
echo.
pause
