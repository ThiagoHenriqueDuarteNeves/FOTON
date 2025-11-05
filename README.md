# 🤖 Agente QA Desktop - FOTON

Agente inteligente de automação QA com interface desktop Electron + React.

## 🚀 Instalação Rápida

### Windows

#### Opção A: Instalador Automático ⚡

```bash
git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git
cd FOTON
git checkout ui-electron-react
cd AgenteIA\agente_qa
instalar.bat
```

**Depois execute**:
```bash
cd frontend
start-electron.bat
```

#### Opção B: Instalação Manual 🔧

Se o script automático falhar, siga o guia passo a passo:
📖 **[INSTALACAO_MANUAL.md](AgenteIA/agente_qa/INSTALACAO_MANUAL.md)**

Ou resumidamente:

```bash
# 1. Clone e entre na pasta
git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git
cd FOTON
git checkout ui-electron-react

# 2. Configure Python (em AgenteIA/)
cd AgenteIA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium

# 3. Configure Node.js (em agente_qa/frontend/)
cd agente_qa\frontend
npm install
npm run build

# 4. Execute
npx electron electron.js
```

### Linux/Mac

1. **Clone o repositório**:
```bash
git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git
cd FOTON
git checkout ui-electron-react
```

2. **Configure o ambiente Python**:
```bash
cd AgenteIA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

3. **Configure o frontend**:
```bash
cd agente_qa/frontend
npm install
npm run build
```

4. **Inicie a aplicação**:
```bash
npx electron electron.js
```

## 📋 Pré-requisitos

- **Node.js** 20+ ([Download](https://nodejs.org/))
- **Python** 3.11+ ([Download](https://www.python.org/))
- **Git** ([Download](https://git-scm.com/))
- **LM Studio** ou **Ollama** (opcional, para modelos locais)

## 📖 Documentação Completa

Veja o guia completo em: [AgenteIA/agente_qa/README.md](AgenteIA/agente_qa/README.md)

## ⚡ Recursos

- ✅ Interface desktop moderna com Electron + React
- ✅ Suporte para múltiplos providers LLM (LM Studio, Ollama, OpenAI)
- ✅ Carregamento dinâmico de modelos
- ✅ Automação de testes com Playwright
- ✅ Modo teste integrado (ParaBank)
- ✅ Interface responsiva
- ✅ Logs em tempo real

## 🎯 Uso Básico

1. **Configure o LLM Provider**:
   - LM Studio: `http://localhost:1234`
   - Ollama: `http://localhost:11434`
   - OpenAI: `https://api.openai.com/v1` + API Key

2. **Carregue os modelos disponíveis** (botão 🔄)

3. **Configure a URL alvo** e instruções

4. **Inicie o agente** (botão ▶️)

## 🐛 Solução de Problemas

Consulte a seção "Solução de Problemas" no [README completo](AgenteIA/agente_qa/README.md).

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/ThiagoHenriqueDuarteNeves/FOTON/issues)
- **Documentação**: Ver pasta `AgenteIA/agente_qa/`

## 📄 Licença

Este projeto está em desenvolvimento ativo.

---

**Branch atual**: `ui-electron-react` (Desktop App)  
**Branch web**: `refatoracao-ui-vite` (Web App com FastAPI)
