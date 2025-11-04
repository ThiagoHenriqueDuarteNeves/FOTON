# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-01-15

### 🎉 Lançamento Inicial

Primeira versão completa do Agente de QA Automatizado com LLM.

### ✨ Adicionado

#### Core Features
- Sistema de navegação automatizada baseado em LLM
- Suporte a múltiplos provedores LLM (LM Studio, Ollama, APIs externas)
- Análise inteligente de HTML e extração de elementos interativos
- Execução de ações no navegador (click, fill, navigate, etc.)
- Sistema de logging completo com rotação automática
- Captura automática de screenshots a cada passo

#### Interfaces
- **CLI**: Interface de linha de comando (`main.py`)
- **Desktop**: Interface gráfica Tkinter (`ui_agente.py`)
- **Web**: Interface moderna React + FastAPI
  - Backend REST API com FastAPI
  - Frontend React com Vite
  - WebSocket para logs em tempo real
  - Teste de conectividade com LLM

#### Módulos do Agente
- `navigation_controller.py`: Controle principal de navegação
- `llm_providers.py`: Abstração de provedores LLM
- `html_parser.py`: Parse e simplificação de HTML
- `browser_actions.py`: Ações do navegador com Playwright
- `form_handler.py`: Manipulação inteligente de formulários
- `action_executor.py`: Execução de ações
- `prompt_generator.py`: Geração de prompts para LLM
- `screenshot_manager.py`: Gerenciamento de capturas de tela
- `response_parser.py`: Parse de respostas do LLM
- E mais 6 módulos especializados

#### Documentação
- `README.md`: Documentação principal completa
- `docs/ARCHITECTURE.md`: Arquitetura detalhada com diagramas
- `docs/API.md`: Documentação completa da API REST
- `docs/DEVELOPMENT.md`: Guia de desenvolvimento
- `docs/SECURITY.md`: Práticas de segurança

#### Scripts Utilitários
- `scripts/start_servers.py`: Iniciar backend e frontend simultaneamente
- `scripts/cleanup.py`: Limpar arquivos temporários e cache
- `scripts/health_check.py`: Verificação de saúde do sistema

#### Configuração
- `pytest.ini`: Configuração completa do pytest
- `pyproject.toml`: Configuração de ferramentas (Black, Ruff, MyPy)
- `tests/conftest.py`: Fixtures compartilhadas para testes
- `.gitignore`: Proteção de arquivos sensíveis

#### Estrutura de Diretórios
```
llm_agent_test/
├── agent/          # Módulos do agente (15+ arquivos)
├── backend/        # API FastAPI
├── frontend/       # Interface React
├── docs/           # Documentação completa
├── tests/          # Testes automatizados
├── scripts/        # Scripts utilitários
├── config/         # Configurações
├── logs/           # Logs de execução
└── prints/         # Screenshots
```

### 🔒 Segurança

- Variáveis de ambiente para credenciais sensíveis
- Sanitização de logs (remove senhas e tokens)
- .gitignore completo protegendo dados sensíveis
- Guia de segurança com best practices
- CORS configurado no backend

### 🧪 Testes

- Estrutura completa de testes (unit, integration, e2e)
- Fixtures reutilizáveis no conftest.py
- Configuração pytest com cobertura de código
- Markers customizados para diferentes tipos de teste

### 📦 Dependências

#### Python
- playwright >= 1.40.0
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- pydantic >= 2.5.0

#### Node.js
- react >= 18.2.0
- vite >= 5.0.0

### 🎨 Qualidade de Código

- Configuração Black para formatação
- Ruff para linting
- MyPy para type checking
- Cobertura de testes > 70%

---

## [Não Lançado]

### 🚀 Planejado

#### Features
- [ ] Sistema de autenticação JWT
- [ ] Histórico de execuções
- [ ] Exportação de relatórios (PDF, HTML)
- [ ] Webhooks para notificações
- [ ] Cache de respostas LLM
- [ ] Suporte a múltiplos browsers simultâneos
- [ ] Modo de gravação de ações
- [ ] Replay de sessões

#### Melhorias
- [ ] Performance: Otimização de parse HTML
- [ ] UI: Modo escuro na interface web
- [ ] Logs: Estruturados em JSON
- [ ] Testes: Aumentar cobertura para > 90%

#### Documentação
- [ ] Tutoriais em vídeo
- [ ] Exemplos de uso avançado
- [ ] FAQ expandido

#### DevOps
- [ ] Docker Compose para deploy completo
- [ ] CI/CD com GitHub Actions
- [ ] Testes automatizados em PRs
- [ ] Deploy automático

---

## Tipos de Mudanças

- `✨ Adicionado` para novas funcionalidades
- `🔄 Modificado` para mudanças em funcionalidades existentes
- `🗑️ Depreciado` para funcionalidades que serão removidas
- `❌ Removido` para funcionalidades removidas
- `🐛 Corrigido` para correções de bugs
- `🔒 Segurança` para vulnerabilidades corrigidas

---

**Legenda de Versões:**
- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis

[1.0.0]: https://github.com/username/llm_agent_test/releases/tag/v1.0.0
