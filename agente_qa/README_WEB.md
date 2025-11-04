# 🤖 Agente de QA Automatizado - Interface Web

Interface web moderna para o Agente de QA Automatizado, construída com **React** (frontend) e **FastAPI** (backend).

## 📋 Requisitos

- Python 3.8+ (já configurado)
- Node.js 18+ e npm
- LM Studio ou outro servidor LLM

## 🚀 Inicialização Rápida

### Opção 1: Scripts Automáticos (Recomendado)

#### 1. Iniciar o Backend (FastAPI)
```bash
cd backend
start_backend.bat
```

O backend estará rodando em:
- API: http://localhost:8000
- Documentação: http://localhost:8000/docs

#### 2. Iniciar o Frontend (React)
Em outro terminal:
```bash
cd frontend
start_frontend.bat
```

O frontend estará rodando em:
- Interface: http://localhost:3000

### Opção 2: Inicialização Manual

#### Backend:
```bash
cd backend
pip install -r requirements.txt
python api.py
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

## 🎯 Funcionalidades

### Interface Web
- ✅ Design moderno e responsivo
- ✅ Configuração completa do agente
- ✅ Seleção de modelos LLM
- ✅ Teste de conexão com LLM
- ✅ Logs em tempo real via WebSocket
- ✅ Controles de execução (Iniciar/Parar)
- ✅ Salvamento de configurações
- ✅ Modo teste automático

### Backend API
- ✅ Endpoints REST para controle do agente
- ✅ WebSocket para logs em tempo real
- ✅ Documentação automática (Swagger)
- ✅ CORS configurado
- ✅ Gerenciamento de estado da execução

## 📚 Endpoints da API

### REST Endpoints

- `GET /` - Informações da API
- `GET /api/models` - Lista modelos disponíveis
- `POST /api/llm/test` - Testa conexão com LLM
- `POST /api/agent/start` - Inicia o agente
- `POST /api/agent/stop` - Para o agente
- `GET /api/agent/status` - Status atual

### WebSocket

- `WS /ws/logs` - Logs em tempo real

Acesse a documentação interativa em: http://localhost:8000/docs

## 🛠️ Tecnologias Utilizadas

### Frontend
- **React 18** - Framework UI
- **Vite** - Build tool moderna e rápida
- **Axios** - Cliente HTTP
- **Lucide React** - Ícones modernos
- **CSS3** - Estilização customizada

### Backend
- **FastAPI** - Framework web assíncrono
- **Uvicorn** - Servidor ASGI
- **WebSockets** - Comunicação em tempo real
- **Pydantic** - Validação de dados

## 📁 Estrutura do Projeto

```
llm_agent_test/
├── backend/
│   ├── api.py              # API FastAPI
│   ├── requirements.txt    # Dependências Python
│   └── start_backend.bat   # Script de inicialização
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Componente principal
│   │   ├── App.css         # Estilos
│   │   └── main.jsx        # Entrada da aplicação
│   ├── index.html          # HTML base
│   ├── package.json        # Dependências Node
│   ├── vite.config.js      # Configuração Vite
│   └── start_frontend.bat  # Script de inicialização
│
├── agent/                  # Módulos do agente (mantidos)
├── main.py                 # Lógica principal (mantida)
└── README_WEB.md          # Este arquivo
```

## 🎨 Recursos da Interface

1. **Configuração Intuitiva**
   - Campos organizados em cards
   - Validação em tempo real
   - Hints e placeholders

2. **Feedback Visual**
   - Indicadores de status
   - Animações suaves
   - Cores semânticas

3. **Logs em Tempo Real**
   - Console estilo terminal
   - Auto-scroll
   - Indicador de conexão

4. **Responsividade**
   - Layout adaptativo
   - Mobile-friendly
   - Grid responsivo

## 🔧 Desenvolvimento

### Build de Produção (Frontend)
```bash
cd frontend
npm run build
```

Os arquivos estáticos serão gerados em `frontend/dist/`

### Testes da API
Acesse http://localhost:8000/docs para testar os endpoints interativamente.

## 📝 Notas

- O backend deve estar rodando para o frontend funcionar
- O WebSocket reconecta automaticamente se a conexão cair
- As configurações podem ser salvas em JSON
- O modo teste configura automaticamente o ParaBank

## 🐛 Solução de Problemas

### Backend não inicia
- Verifique se a porta 8000 está livre
- Certifique-se que as dependências foram instaladas

### Frontend não carrega
- Verifique se o Node.js está instalado
- Execute `npm install` no diretório frontend
- Certifique-se que a porta 3000 está livre

### WebSocket não conecta
- Verifique se o backend está rodando
- Verifique o console do navegador para erros

## 🚀 Próximos Passos

- [ ] Autenticação de usuários
- [ ] Histórico de execuções
- [ ] Gráficos e métricas
- [ ] Temas customizáveis
- [ ] Deploy em produção

---

**Desenvolvido com ❤️ usando React + FastAPI**
