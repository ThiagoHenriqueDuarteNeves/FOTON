# 📂 Estrutura do Projeto - Guia Visual

## 🗂️ Árvore de Diretórios

```
FOTON/                                  ← Raiz do repositório Git
│
├── 📄 README.md                        ← Você está aqui! Início rápido
│
└── AgenteIA/                           ← Diretório principal da aplicação
    │
    ├── 📄 requirements.txt             ← Dependências Python
    │
    ├── 📁 .venv/                       ← Ambiente virtual Python (criado na instalação)
    │   ├── Scripts/
    │   │   ├── activate.bat            ← Ativar ambiente (CMD)
    │   │   ├── Activate.ps1            ← Ativar ambiente (PowerShell)
    │   │   └── python.exe              ← Python isolado
    │   └── Lib/                        ← Pacotes instalados
    │
    ├── 📁 llm_agent_test/              ← Código Python do agente
    │   ├── main.py                     ← Entry point do agente Python
    │   ├── agent.py                    ← Lógica do agente
    │   └── ...                         ← Outros módulos
    │
    └── 📁 agente_qa/                   ← Aplicação Desktop
        │
        ├── 📄 README.md                ← Documentação completa
        ├── 📄 INSTALACAO_MANUAL.md     ← Guia passo a passo
        ├── 📄 CHECKLIST.md             ← Checklist de verificação
        ├── 📄 instalar.bat             ← Script de instalação (Windows)
        │
        └── 📁 frontend/                ← Aplicação Electron + React
            │
            ├── 📄 package.json         ← Dependências Node.js
            ├── 📄 electron.js          ← Processo principal Electron
            ├── 📄 preload.js           ← Bridge de segurança
            ├── 📄 start-electron.bat   ← Script para iniciar
            │
            ├── 📁 src/                 ← Código-fonte React
            │   ├── App.jsx             ← Componente principal
            │   ├── App.css             ← Estilos
            │   └── main.jsx            ← Entry point React
            │
            ├── 📁 dist/                ← Build do React (gerado por npm run build)
            │   ├── index.html          ← HTML final
            │   └── assets/             ← JS e CSS minificados
            │       ├── index-*.js
            │       └── index-*.css
            │
            └── 📁 node_modules/        ← Pacotes Node.js (gerado por npm install)
                ├── electron/
                ├── react/
                └── ... (milhares de pacotes)
```

## 🎯 Onde Estar em Cada Etapa

### 📍 Etapa 1: Clone

```
Você executa:    git clone ...
Você fica em:    FOTON/                    ← Raiz
```

### 📍 Etapa 2: Python

```
Você navega:     cd AgenteIA
Você está em:    FOTON/AgenteIA/           ← Cria .venv aqui
Você executa:    python -m venv .venv
                 .venv\Scripts\activate.bat
                 pip install -r requirements.txt
```

### 📍 Etapa 3: Node.js

```
Você navega:     cd agente_qa\frontend
Você está em:    FOTON/AgenteIA/agente_qa/frontend/  ← Instala node_modules aqui
Você executa:    npm install
                 npm run build              ← Cria pasta dist/
```

### 📍 Etapa 4: Executar

```
Você está em:    FOTON/AgenteIA/agente_qa/frontend/
Você executa:    start-electron.bat
                 OU
                 npx electron electron.js
```

## 🔍 Como Saber se Está no Lugar Certo

### ✅ No lugar certo para Python:
```powershell
PS C:\...\FOTON\AgenteIA>
```
Deve existir aqui:
- ✓ `requirements.txt`
- ✓ `llm_agent_test/`
- ✓ `agente_qa/`

### ✅ No lugar certo para Node.js:
```powershell
PS C:\...\FOTON\AgenteIA\agente_qa\frontend>
```
Deve existir aqui:
- ✓ `package.json`
- ✓ `electron.js`
- ✓ `src/`

### ✅ No lugar certo para Executar:
```powershell
PS C:\...\FOTON\AgenteIA\agente_qa\frontend>
```
Deve existir aqui:
- ✓ `dist/` (pasta com o build)
- ✓ `node_modules/` (pasta com dependências)
- ✓ `start-electron.bat`

## 🚫 Erros Comuns de Navegação

### ❌ ERRO: "requirements.txt não encontrado"

**Você está em**: `FOTON/agente_qa/` ou `FOTON/`  
**Deveria estar em**: `FOTON/AgenteIA/`

**Correção**:
```bash
cd AgenteIA
```

### ❌ ERRO: "package.json não encontrado"

**Você está em**: `FOTON/AgenteIA/` ou `FOTON/agente_qa/`  
**Deveria estar em**: `FOTON/AgenteIA/agente_qa/frontend/`

**Correção**:
```bash
cd agente_qa\frontend
```

### ❌ ERRO: "electron.js não encontrado"

**Você está em**: Qualquer lugar exceto frontend/  
**Deveria estar em**: `FOTON/AgenteIA/agente_qa/frontend/`

**Correção a partir da raiz**:
```bash
cd AgenteIA\agente_qa\frontend
```

### ❌ ERRO: "dist não encontrado"

**Causa**: Você não executou `npm run build`

**Solução**:
```bash
# Certifique-se de estar em frontend/
cd AgenteIA\agente_qa\frontend

# Execute o build
npm run build

# Verifique que criou
dir dist
```

## 📊 Fluxo de Execução

```
1. USUÁRIO CLICA: "Iniciar Agente"
   └── Interface React (frontend/src/App.jsx)
       │
       ├── 2. IPC: window.electronAPI.runPythonScript(...)
       │   └── preload.js: contextBridge expõe API
       │       │
       │       └── 3. Electron Main Process (electron.js)
       │           └── ipcMain.handle('run-python-script')
       │               │
       │               └── 4. Spawns Python Process
       │                   └── python AgenteIA/llm_agent_test/main.py
       │                       │
       │                       ├── 5. Playwright abre navegador
       │                       ├── 6. LLM analisa e decide ações
       │                       └── 7. Executa ações no navegador
       │                           │
       │                           └── 8. Output → stdout
       │                               │
       │                               └── 9. Electron captura output
       │                                   └── ipcRenderer.send('python-output')
       │                                       │
       │                                       └── 10. React atualiza logs
```

## 🎨 Tecnologias por Camada

```
┌─────────────────────────────────────────┐
│  INTERFACE (React + Vite)               │
│  📁 frontend/src/                        │
│  • App.jsx, App.css                     │
│  • lucide-react (ícones)                │
└─────────────────────────────────────────┘
                  ↕️ IPC
┌─────────────────────────────────────────┐
│  DESKTOP (Electron)                     │
│  📁 frontend/                            │
│  • electron.js (main process)           │
│  • preload.js (security bridge)         │
└─────────────────────────────────────────┘
                  ↕️ spawn
┌─────────────────────────────────────────┐
│  AGENTE (Python)                        │
│  📁 llm_agent_test/                      │
│  • main.py (CLI)                        │
│  • agent.py (lógica)                    │
│  • Playwright (automação)               │
│  • OpenAI/Anthropic (LLM)               │
└─────────────────────────────────────────┘
                  ↕️ HTTP
┌─────────────────────────────────────────┐
│  LLM PROVIDER                           │
│  • LM Studio (localhost:1234)           │
│  • Ollama (localhost:11434)             │
│  • OpenAI API (api.openai.com)          │
└─────────────────────────────────────────┘
```

## 🔐 Arquivos de Configuração

```
📄 package.json                    → Dependências Node.js, scripts npm
📄 requirements.txt                → Dependências Python
📄 .env (opcional)                 → Variáveis de ambiente, API keys
📄 vite.config.js                  → Configuração do build React
```

## 📦 Arquivos Gerados (Ignorados pelo Git)

```
.venv/                → Ambiente virtual Python (criado por: python -m venv .venv)
node_modules/         → Pacotes Node.js (criado por: npm install)
dist/                 → Build React (criado por: npm run build)
__pycache__/          → Cache Python (criado automaticamente)
*.pyc                 → Bytecode Python (criado automaticamente)
```

## 🎯 Comandos por Localização

```
📍 FOTON/
  • git clone, git checkout, git pull

📍 FOTON/AgenteIA/
  • python -m venv .venv
  • .venv\Scripts\activate.bat
  • pip install -r requirements.txt
  • playwright install chromium

📍 FOTON/AgenteIA/agente_qa/frontend/
  • npm install
  • npm run build
  • npx electron electron.js
  • start-electron.bat
```

## 💡 Dica de Navegação

Use sempre **caminhos absolutos** ou saiba exatamente onde está:

```bash
# Ver onde você está
pwd        # Linux/Mac
cd         # Windows

# Ver o que tem na pasta atual
ls         # Linux/Mac
dir        # Windows

# Voltar para a raiz do projeto
cd C:\caminho\para\FOTON
```

---

**Lembre-se**: Cada tecnologia tem seu "lugar":
- **Python** = `AgenteIA/`
- **Node.js** = `agente_qa/frontend/`
- **Git** = `FOTON/` (raiz)
