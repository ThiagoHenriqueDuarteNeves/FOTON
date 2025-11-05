# ✅ Checklist de Verificação - Novo Computador

Use este checklist para garantir que tudo está configurado corretamente.

## 📦 Pré-Instalação

### Software Necessário

- [ ] **Node.js** instalado
  - Comando de teste: `node --version`
  - Versão esperada: v20.x.x ou superior
  - Download: https://nodejs.org/

- [ ] **Python** instalado
  - Comando de teste: `python --version`
  - Versão esperada: 3.11.x ou superior
  - Download: https://www.python.org/
  - ⚠️ IMPORTANTE: Marcar "Add Python to PATH" na instalação

- [ ] **Git** instalado
  - Comando de teste: `git --version`
  - Download: https://git-scm.com/

- [ ] **LM Studio** ou **Ollama** (opcional, se usar modelos locais)
  - LM Studio: https://lmstudio.ai/
  - Ollama: https://ollama.ai/

## 🔧 Instalação

### 1. Clonar Repositório

- [ ] Repositório clonado
  ```bash
  git clone https://github.com/ThiagoHenriqueDuarteNeves/FOTON.git
  cd FOTON
  ```

- [ ] Branch correto selecionado
  ```bash
  git checkout ui-electron-react
  ```

### 2. Backend Python

- [ ] Navegou para o diretório AgenteIA
  ```bash
  cd AgenteIA
  ```

- [ ] Ambiente virtual criado
  ```bash
  python -m venv .venv
  ```

- [ ] Ambiente virtual ativado
  ```bash
  # Windows PowerShell:
  .\.venv\Scripts\Activate.ps1
  
  # Windows CMD:
  .venv\Scripts\activate.bat
  ```

- [ ] Dependências instaladas
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Playwright browsers instalados
  ```bash
  playwright install chromium
  ```

- [ ] Teste do Python (deve mostrar versão)
  ```bash
  python -c "import playwright; print('OK')"
  ```

### 3. Frontend Electron

- [ ] Navegou para o diretório frontend
  ```bash
  cd agente_qa\frontend
  ```

- [ ] Dependências Node.js instaladas
  ```bash
  npm install
  ```

- [ ] Build executado com sucesso
  ```bash
  npm run build
  ```

- [ ] Pasta `dist/` foi criada
  - Verifique se existe: `frontend/dist/index.html`

## 🎯 Configuração LLM

### Opção A: LM Studio (Local)

- [ ] LM Studio instalado
- [ ] Modelo baixado (ex: qwen2.5-coder, llama)
- [ ] Servidor local iniciado
- [ ] Teste do servidor: Abrir `http://localhost:1234/v1/models` no navegador
- [ ] Resposta deve ser JSON com lista de modelos

### Opção B: Ollama (Local)

- [ ] Ollama instalado
- [ ] Modelo baixado
  ```bash
  ollama pull llama3.2
  ```
- [ ] Teste do servidor: `ollama list`
- [ ] Modelos aparecem na lista

### Opção C: OpenAI/API Externa

- [ ] API Key obtida
- [ ] URL da API conhecida (ex: https://api.openai.com/v1)
- [ ] Modelo conhecido (ex: gpt-4o-mini)

## ▶️ Primeiro Teste

### Executar Aplicação

- [ ] Aplicação inicia sem erros
  ```bash
  cd frontend
  .\start-electron.bat
  ```
  Ou: `npx electron electron.js`

### Interface

- [ ] Janela Electron abre
- [ ] Interface aparece corretamente
- [ ] Sem erros no console (F12)

### Configuração

- [ ] Provider LLM selecionado
- [ ] URL do LLM configurada
- [ ] API Key inserida (se necessário)
- [ ] Botão 🔄 carrega modelos
- [ ] Modelos aparecem no dropdown

### Teste Funcional

- [ ] Modo Teste (ParaBank) marcado
- [ ] Botão "Iniciar Agente" funciona
- [ ] Logs aparecem em tempo real
- [ ] Processo completa sem erros
- [ ] Browser Playwright abre e fecha automaticamente

## 🐛 Troubleshooting

### Se algo falhar, verifique:

#### Erro: "Python não encontrado"
- [ ] Python está no PATH do sistema
- [ ] Reiniciei o terminal após instalar Python
- [ ] Tentei `py --version` em vez de `python --version`

#### Erro: "node não é reconhecido"
- [ ] Node.js foi instalado corretamente
- [ ] Reiniciei o terminal após instalar Node.js
- [ ] Path do Node.js está em variáveis de ambiente

#### Erro: "npm install falha"
- [ ] Executei `npm cache clean --force`
- [ ] Removi pasta `node_modules`
- [ ] Tentei `npm install` novamente
- [ ] Verifiquei conexão com internet

#### Erro: "Playwright browser not found"
- [ ] Ambiente virtual Python está ativado
- [ ] Executei `playwright install chromium`
- [ ] Tentei `playwright install --force`

#### Erro: "Modelos não carregam"
- [ ] LM Studio/Ollama está rodando
- [ ] Servidor está na porta correta (1234 ou 11434)
- [ ] Testei URL no navegador
- [ ] Firewall não está bloqueando

#### Erro: "start-electron.bat não funciona"
- [ ] Estou no diretório correto (`frontend/`)
- [ ] Build foi executado (`npm run build`)
- [ ] Pasta `dist/` existe e tem arquivos
- [ ] Tentei `npx electron electron.js` diretamente

## 📊 Status Final

### Checklist Resumido

- [ ] ✅ Todos os softwares instalados
- [ ] ✅ Repositório clonado e branch correto
- [ ] ✅ Backend Python configurado
- [ ] ✅ Frontend Node.js configurado
- [ ] ✅ LLM Provider configurado
- [ ] ✅ Aplicação executa sem erros
- [ ] ✅ Teste funcional passou

### Comandos de Verificação Rápida

Execute todos estes comandos para verificação final:

```bash
# Verificar versões
node --version
python --version
git --version

# Verificar ambiente Python
cd AgenteIA
.\.venv\Scripts\Activate.ps1
python -c "import playwright, openai; print('Pacotes OK')"

# Verificar Node.js
cd agente_qa\frontend
npm list electron --depth=0

# Verificar LM Studio/Ollama
curl http://localhost:1234/v1/models
# OU
curl http://localhost:11434/api/tags
```

## 🎉 Sucesso!

Se todos os itens estão marcados, você está pronto para usar o Agente QA Desktop!

### Próximos Passos

1. Execute a aplicação: `.\start-electron.bat`
2. Configure suas preferências
3. Faça um teste com ParaBank
4. Comece a usar em projetos reais

---

**Dica**: Salve este checklist para referência futura ou para instalar em outros computadores!
