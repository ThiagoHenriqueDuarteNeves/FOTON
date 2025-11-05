# 🚀 Instalação Manual - Passo a Passo

Se o script automático não funcionar, siga estes passos manualmente.

## 📍 IMPORTANTE: Estrutura de Diretórios

Após clonar, você deve ter:
```
FOTON/
├── AgenteIA/
│   ├── .venv/              ← Ambiente virtual (será criado)
│   ├── requirements.txt    ← Dependências Python
│   ├── llm_agent_test/
│   └── agente_qa/
│       ├── frontend/
│       │   ├── package.json
│       │   ├── electron.js
│       │   └── src/
│       └── instalar.bat
```

## 1️⃣ Clone e Navegue

```bash
# Clone o repositório
git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git

# Entre na pasta
cd FOTON

# Mude para a branch correta
git checkout ui-electron-react

# Verifique que está no lugar certo
# Você deve ver as pastas: AgenteIA, docs, etc.
dir
```

## 2️⃣ Configure o Python

```bash
# Entre na pasta AgenteIA (onde fica o Python)
cd AgenteIA

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# No PowerShell:
.\.venv\Scripts\Activate.ps1

# No CMD:
.venv\Scripts\activate.bat

# Você deve ver (.venv) no início da linha do terminal

# Atualize o pip
python -m pip install --upgrade pip

# Instale as dependências
pip install -r requirements.txt

# Instale os navegadores do Playwright
playwright install chromium

# Teste se funcionou
python -c "import playwright; print('✓ Playwright OK')"
```

## 3️⃣ Configure o Node.js

```bash
# Entre na pasta do frontend (A PARTIR de AgenteIA)
cd agente_qa\frontend

# Instale as dependências
npm install

# Se der erro, tente:
npm cache clean --force
npm install

# Faça o build
npm run build

# Verifique se criou a pasta dist
dir dist

# Você deve ver: index.html e uma pasta assets
```

## 4️⃣ Execute a Aplicação

```bash
# Certifique-se que está em: FOTON/AgenteIA/agente_qa/frontend
# Execute o Electron
npx electron electron.js

# Ou use o script:
.\start-electron.bat
```

## ✅ Verificação de Cada Passo

### Após Passo 1 (Clone):
```bash
# Você está aqui:
C:\...\FOTON

# Deve existir:
dir AgenteIA
```

### Após Passo 2 (Python):
```bash
# Você está aqui:
C:\...\FOTON\AgenteIA

# Ambiente ativado (veja o (.venv) no prompt):
(.venv) PS C:\...\FOTON\AgenteIA>

# Teste:
python -c "import playwright; print('OK')"
```

### Após Passo 3 (Node.js):
```bash
# Você está aqui:
C:\...\FOTON\AgenteIA\agente_qa\frontend

# Deve existir:
dir dist
dir node_modules
```

### Após Passo 4 (Executar):
```bash
# Uma janela Electron deve abrir com a interface
```

## 🐛 Soluções para Erros Comuns

### "python não é reconhecido"

**Causa**: Python não está no PATH

**Solução**:
1. Abra um **novo terminal** (importante!)
2. Tente `py --version` em vez de `python --version`
3. Se não funcionar, reinstale Python marcando "Add to PATH"

### "npm não é reconhecido"

**Causa**: Node.js não está no PATH

**Solução**:
1. Abra um **novo terminal**
2. Verifique instalação: `node --version`
3. Se não funcionar, reinstale Node.js

### "playwright install chromium" demora muito

**Causa**: Download grande (~300MB)

**Solução**:
- Aguarde, é normal demorar 5-10 minutos
- Verifique sua conexão com internet

### "npm install" falha com erros de rede

**Solução**:
```bash
# Limpe o cache
npm cache clean --force

# Configure timeout maior
npm config set fetch-timeout 60000

# Tente novamente
npm install
```

### "dist não foi criado"

**Causa**: Build falhou

**Solução**:
```bash
# Veja o erro completo
npm run build

# Se faltar dependências:
npm install

# Tente novamente
npm run build
```

### ".venv\Scripts\activate.bat não encontrado"

**Causa**: Ambiente virtual não foi criado corretamente

**Solução**:
```bash
# Remova o ambiente virtual
rmdir /s .venv

# Crie novamente
python -m venv .venv

# Tente ativar
.venv\Scripts\activate.bat
```

### "Electron abre mas não mostra interface"

**Causa**: Build não foi feito ou está desatualizado

**Solução**:
```bash
cd AgenteIA\agente_qa\frontend
npm run build
npx electron electron.js
```

## 📝 Comandos de Diagnóstico

Se algo não funcionar, execute estes comandos e me mostre a saída:

```bash
# Verificar versões
node --version
python --version
npm --version

# Verificar estrutura
cd FOTON
dir
cd AgenteIA
dir
cd agente_qa\frontend
dir

# Verificar ambiente Python
cd ..\..
.venv\Scripts\activate.bat
python -c "import sys; print(sys.executable)"
pip list

# Verificar Node.js
cd agente_qa\frontend
npm list --depth=0
```

## 🎯 Resumo dos Caminhos

```
1. Clone:     qualquer lugar
2. Python:    FOTON/AgenteIA/
3. Node.js:   FOTON/AgenteIA/agente_qa/frontend/
4. Executar:  FOTON/AgenteIA/agente_qa/frontend/
```

## 💡 Dica Final

Se preferir, faça **um passo de cada vez** e teste antes de continuar para o próximo. Não pule verificações!

1. ✅ Clone → Verifique pasta AgenteIA
2. ✅ Python → Teste import playwright
3. ✅ Node.js → Verifique pasta dist
4. ✅ Execute → Janela deve abrir

Qualquer erro, anote a mensagem completa e consulte a seção de soluções acima!
