# Development Guide

## 🛠️ Configuração do Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.8+
- Node.js 16+
- Git
- VS Code (recomendado)

### Configuração Inicial

```bash
# 1. Clone o repositório
git clone <repository-url>
cd llm_agent_test

# 2. Configure Python
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

# 3. Configure Node.js
cd frontend
npm install
cd ..

# 4. Configure variáveis de ambiente
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edite .env com suas configurações
```

### Extensões VS Code Recomendadas

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "dsznajder.es7-react-js-snippets",
    "bradlc.vscode-tailwindcss",
    "ms-playwright.playwright"
  ]
}
```

---

## 🏗️ Estrutura do Projeto

```
llm_agent_test/
├── agent/                  # Módulos do agente
│   ├── __init__.py
│   ├── action_executor.py  # Execução de ações
│   ├── browser_actions.py  # Ações do navegador
│   ├── form_handler.py     # Manipulação de formulários
│   ├── html_parser.py      # Parse e simplificação HTML
│   ├── llm_providers.py    # Provedores LLM
│   ├── navigation_controller.py  # Controle de navegação
│   └── ...
├── backend/                # API FastAPI
│   ├── api.py             # Rotas e endpoints
│   └── ...
├── frontend/              # Interface React
│   ├── src/
│   │   ├── App.jsx       # Componente principal
│   │   ├── App.css       # Estilos
│   │   └── main.jsx      # Entry point
│   ├── package.json
│   └── vite.config.js
├── docs/                  # Documentação
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   └── SECURITY.md
├── tests/                 # Testes automatizados
├── scripts/               # Scripts utilitários
├── config/                # Arquivos de configuração
├── logs/                  # Logs de execução
├── prints/                # Screenshots
├── main.py                # CLI principal
├── ui_agente.py          # Interface Tkinter
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente
└── README.md              # Documentação principal
```

---

## 🔧 Workflows de Desenvolvimento

### Adicionando Nova Funcionalidade

1. **Criar Branch**
```bash
git checkout -b feature/nome-da-feature
```

2. **Desenvolver com TDD**
```python
# tests/test_nova_feature.py
def test_nova_funcionalidade():
    # Arrange
    agente = NovaFuncionalidade()
    
    # Act
    resultado = agente.executar()
    
    # Assert
    assert resultado == esperado
```

3. **Implementar Feature**
```python
# agent/nova_feature.py
class NovaFuncionalidade:
    def executar(self):
        # Implementação
        pass
```

4. **Executar Testes**
```bash
pytest tests/test_nova_feature.py -v
```

5. **Verificar Cobertura**
```bash
pytest --cov=agent --cov-report=html
```

6. **Lint e Format**
```bash
black agent/
ruff check agent/
mypy agent/
```

7. **Commit e Push**
```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
git push origin feature/nome-da-feature
```

8. **Criar Pull Request**

---

## 🧪 Testing

### Estrutura de Testes

```
tests/
├── unit/                  # Testes unitários
│   ├── test_llm_providers.py
│   ├── test_html_parser.py
│   └── test_form_handler.py
├── integration/           # Testes de integração
│   ├── test_navigation_flow.py
│   └── test_api_endpoints.py
├── e2e/                   # Testes end-to-end
│   ├── test_complete_navigation.py
│   └── test_web_interface.py
└── conftest.py            # Fixtures compartilhadas
```

### Executando Testes

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Com cobertura
pytest --cov=agent --cov-report=html

# Modo watch
pytest-watch

# Verbose
pytest -v -s
```

### Exemplos de Testes

#### Teste Unitário

```python
# tests/unit/test_html_parser.py
import pytest
from agent.html_parser import HTMLParser

@pytest.fixture
def parser():
    return HTMLParser()

def test_extract_buttons(parser):
    html = '<button id="btn">Click me</button>'
    elements = parser.extract_interactive_elements(html)
    
    assert len(elements) == 1
    assert elements[0]['tag'] == 'button'
    assert elements[0]['id'] == 'btn'

def test_simplify_html(parser):
    html = '<div><p>Text</p><button>Click</button></div>'
    simplified = parser.simplify(html)
    
    assert '<p>' not in simplified
    assert '<button>' in simplified
```

#### Teste de Integração

```python
# tests/integration/test_navigation_flow.py
import pytest
from playwright.sync_api import sync_playwright
from agent.navigation_controller import NavigationController
from agent.llm_providers import MockLLMProvider

@pytest.fixture
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

def test_complete_navigation(browser):
    page = browser.new_page()
    llm = MockLLMProvider()
    controller = NavigationController(page, llm, max_steps=10)
    
    result = controller.navigate(
        url='https://example.com',
        instructions='Encontre o link de contato'
    )
    
    assert result['status'] == 'success'
    assert result['steps'] > 0
```

#### Teste E2E

```python
# tests/e2e/test_complete_navigation.py
import pytest
from playwright.sync_api import sync_playwright
from agent.main_agent import MainAgent

@pytest.mark.e2e
def test_login_flow():
    agent = MainAgent(headless=True)
    
    result = agent.execute(
        url='https://example.com/login',
        instructions='Faça login com usuário test@test.com e senha test123'
    )
    
    assert result['completed']
    assert 'Dashboard' in result['final_page_title']
```

---

## 🎨 Code Style

### Python

#### Black (Formatter)

```bash
# Formatar todos os arquivos
black .

# Verificar sem modificar
black . --check

# Configuração em pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38']
```

#### Ruff (Linter)

```bash
# Verificar código
ruff check .

# Auto-fix
ruff check . --fix

# Configuração em pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]
```

#### MyPy (Type Checking)

```bash
# Verificar tipos
mypy agent/

# Configuração em pyproject.toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
```

#### Docstrings

```python
def navigate(self, url: str, instructions: str) -> dict:
    """
    Navega até uma URL e executa instruções.
    
    Args:
        url: URL inicial para navegação
        instructions: Instruções em linguagem natural
        
    Returns:
        Dicionário com status da execução:
        {
            'status': 'success' | 'error',
            'steps': int,
            'message': str
        }
        
    Raises:
        NavigationError: Se a navegação falhar
        LLMError: Se o LLM não responder
        
    Examples:
        >>> controller.navigate(
        ...     'https://example.com',
        ...     'Encontre o botão de login'
        ... )
        {'status': 'success', 'steps': 5}
    """
    pass
```

### JavaScript/React

#### Prettier (Formatter)

```bash
# Formatar
npm run format

# Verificar
npm run format:check

# .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80
}
```

#### ESLint

```bash
# Verificar
npm run lint

# Auto-fix
npm run lint:fix

# .eslintrc
{
  "extends": ["react-app", "plugin:prettier/recommended"],
  "rules": {
    "no-console": "warn"
  }
}
```

---

## 🐛 Debugging

### Python

#### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "FastAPI Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "backend.api:app",
        "--reload",
        "--port",
        "8000"
      ]
    }
  ]
}
```

#### Logging

```python
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usar
logger.debug('Informação de debug')
logger.info('Informação geral')
logger.warning('Aviso')
logger.error('Erro')
logger.critical('Erro crítico')
```

#### Breakpoints e pdb

```python
# Inserir breakpoint
import pdb; pdb.set_trace()

# Ou usar breakpoint() (Python 3.7+)
breakpoint()

# Comandos pdb
# n - next line
# s - step into
# c - continue
# p variable - print variable
# l - list source code
# q - quit
```

### React

#### React DevTools

```bash
# Instalar extensão do browser
# Chrome: https://chrome.google.com/webstore
# Firefox: https://addons.mozilla.org
```

#### Console Debugging

```javascript
// Console logging
console.log('Debug info:', variable);
console.warn('Warning:', issue);
console.error('Error:', error);
console.table(arrayOfObjects);

// Debugger
debugger; // Browser irá pausar aqui

// Performance
console.time('Operation');
// ... código
console.timeEnd('Operation');
```

---

## 📦 Build e Deploy

### Backend

```bash
# Desenvolvimento
uvicorn backend.api:app --reload --port 8000

# Produção com Gunicorn
gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend

```bash
# Desenvolvimento
cd frontend
npm run dev

# Build para produção
npm run build

# Preview do build
npm run preview
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright
RUN playwright install --with-deps chromium

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
      - ./prints:/app/prints
    
  frontend:
    image: node:16
    working_dir: /app
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
```

---

## 🔄 Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
        
    - name: Run tests
      run: pytest --cov=agent
      
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 📚 Recursos de Aprendizado

### Documentação Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Playwright](https://playwright.dev/)
- [Pytest](https://docs.pytest.org/)

### Tutoriais Recomendados

- [Python Testing with Pytest](https://realpython.com/pytest-python-testing/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

---

**Happy Coding! 🚀**
