# Agente QA Desktop - Guia de Instalação

## 📋 Pré-requisitos

Antes de começar, você precisa ter instalado:

1. **Node.js** (versão 20 ou superior)
   - Download: https://nodejs.org/
   - Verificar instalação: `node --version`

2. **Python** (versão 3.11 ou superior)
   - Download: https://www.python.org/downloads/
   - **IMPORTANTE**: Marcar "Add Python to PATH" durante a instalação
   - Verificar instalação: `python --version`

3. **Git** (para clonar o repositório)
   - Download: https://git-scm.com/
   - Verificar instalação: `git --version`

4. **LM Studio** (para modelos locais)
   - Download: https://lmstudio.ai/
   - Ou use Ollama: https://ollama.ai/

## 🚀 Instalação Passo a Passo

### 1. Clonar o Repositório

```bash
git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git
cd FOTON
git checkout ui-electron-react
```

### 2. Configurar o Backend Python

```bash
# Navegar para o diretório do agente
cd AgenteIA

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# No Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# No Windows CMD:
.venv\Scripts\activate.bat

# No Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium
```

**Nota sobre requirements.txt**: Se o arquivo não existir, instale manualmente:
```bash
pip install playwright python-dotenv openai anthropic google-generativeai
```

### 3. Configurar o Frontend Electron

```bash
# Navegar para o diretório do frontend
cd agente_qa\frontend

# Instalar dependências do Node.js
npm install

# Fazer o build da aplicação React
npm run build
```

### 4. Configurar o LM Studio (Opcional)

Se quiser usar modelos locais:

1. Abra o **LM Studio**
2. Baixe um modelo (recomendado: qwen2.5-coder ou llama)
3. Vá em **Local Server** → **Start Server**
4. Confirme que está rodando em: `http://localhost:1234`

**Alternativa - Ollama**:
```bash
# Instalar Ollama
# Baixar de: https://ollama.ai/

# Baixar um modelo
ollama pull llama3.2

# Verificar modelos instalados
ollama list
```

## ▶️ Executando a Aplicação

### No Windows:

```bash
# Certifique-se de estar no diretório frontend
cd C:\caminho\para\FOTON\AgenteIA\agente_qa\frontend

# Executar o Electron
.\start-electron.bat
```

Ou manualmente:
```bash
npx electron electron.js
```

### No Linux/Mac:

```bash
# Navegar para o diretório frontend
cd /caminho/para/FOTON/AgenteIA/agente_qa/frontend

# Executar o Electron
npm run electron
```

Ou adicionar script no `package.json`:
```json
{
  "scripts": {
    "electron": "electron electron.js"
  }
}
```

## 🔧 Configuração da Aplicação

Quando a aplicação abrir:

### 1. Configurar Provider LLM

**Opção A - LM Studio (Local)**:
- Provider: `LM Studio`
- URL: `http://localhost:1234`
- API Key: (deixar vazio)
- Clique em 🔄 para carregar modelos

**Opção B - Ollama (Local)**:
- Provider: `Ollama`
- URL: `http://localhost:11434`
- API Key: (deixar vazio)
- Clique em 🔄 para carregar modelos

**Opção C - OpenAI/Externo**:
- Provider: `API Externa (OpenAI, etc)`
- URL: `https://api.openai.com/v1`
- API Key: `sua-chave-api-aqui`
- Modelo: Digite manualmente (ex: `gpt-4o-mini`)

### 2. Testar a Aplicação

Para um teste rápido:
1. Marque ✅ **Modo Teste (ParaBank)**
2. Clique em ▶️ **Iniciar Agente**
3. Aguarde o resultado nos logs

## 📁 Estrutura de Pastas

```
FOTON/
├── AgenteIA/
│   ├── .venv/                    # Ambiente virtual Python
│   ├── llm_agent_test/
│   │   ├── main.py              # Script principal Python
│   │   └── ...
│   ├── agente_qa/
│   │   └── frontend/
│   │       ├── electron.js      # Processo principal Electron
│   │       ├── preload.js       # Bridge de segurança
│   │       ├── src/
│   │       │   ├── App.jsx      # Interface React
│   │       │   └── App.css      # Estilos
│   │       ├── dist/            # Build do React (gerado)
│   │       └── package.json
│   └── requirements.txt
└── README.md
```

## ❓ Solução de Problemas

### Erro: "Python não encontrado"

**Solução**:
1. Verifique se Python está no PATH: `python --version`
2. No Windows, tente `py --version`
3. Reinstale Python marcando "Add to PATH"

### Erro: "Modelos não carregam do LM Studio"

**Solução**:
1. Verifique se o servidor está rodando: abra `http://localhost:1234/v1/models` no navegador
2. Certifique-se que o LM Studio está com o servidor ativo
3. Tente reiniciar o LM Studio

### Erro: "npm install falha"

**Solução**:
1. Limpe o cache: `npm cache clean --force`
2. Remova node_modules: `rm -rf node_modules`
3. Tente novamente: `npm install`

### Erro: "Playwright browser não encontrado"

**Solução**:
```bash
# Ativar ambiente virtual primeiro
.\.venv\Scripts\Activate.ps1

# Instalar browsers
playwright install chromium
```

### Erro: "Permission denied" no Linux/Mac

**Solução**:
```bash
# Dar permissão ao script
chmod +x start-electron.sh

# Ou executar diretamente
npx electron electron.js
```

## 🔄 Atualizando a Aplicação

```bash
# Navegar para o repositório
cd FOTON

# Baixar atualizações
git pull origin ui-electron-react

# Atualizar dependências Python
cd AgenteIA
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Atualizar dependências Node.js
cd agente_qa\frontend
npm install

# Rebuild da aplicação
npm run build
```

## 📦 Criando Executável (Opcional)

Para distribuir sem precisar instalar Node.js:

```bash
# Instalar electron-builder
npm install --save-dev electron-builder

# Adicionar ao package.json:
{
  "build": {
    "appId": "com.foton.agenteqa",
    "win": {
      "target": "portable"
    }
  }
}

# Criar executável
npm run build
npx electron-builder
```

O executável estará em `dist/` (Windows: `.exe`, Linux: `.AppImage`, Mac: `.dmg`)

## 📞 Suporte

- **GitHub Issues**: https://github.com/ThiagoHenriqueDuarteNeves/FOTON/issues
- **Documentação Playwright**: https://playwright.dev/python/
- **Documentação Electron**: https://www.electronjs.org/docs

## 📝 Notas Importantes

1. **Ambiente Virtual**: Sempre ative o ambiente virtual Python antes de executar
2. **Build**: Execute `npm run build` após qualquer mudança no código React
3. **LM Studio**: O servidor precisa estar rodando antes de iniciar a aplicação
4. **Firewall**: Certifique-se que as portas 1234 (LM Studio) e 11434 (Ollama) estão abertas
5. **Antivírus**: Alguns antivírus podem bloquear o Electron - adicione exceção se necessário

## 🎯 Checklist de Instalação

- [ ] Node.js instalado e funcionando
- [ ] Python instalado e no PATH
- [ ] Git instalado
- [ ] Repositório clonado
- [ ] Ambiente virtual Python criado e ativado
- [ ] Dependências Python instaladas (`pip install -r requirements.txt`)
- [ ] Playwright browsers instalados (`playwright install chromium`)
- [ ] Dependências Node.js instaladas (`npm install`)
- [ ] Build React executado (`npm run build`)
- [ ] LM Studio ou Ollama configurado (se usar local)
- [ ] Aplicação inicia sem erros (`.\start-electron.bat`)

✅ **Pronto! Você está pronto para usar o Agente QA Desktop!**
