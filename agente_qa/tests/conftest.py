# tests/conftest.py - Fixtures compartilhadas do pytest

import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
from unittest.mock import Mock

# Fixtures de Browser/Page

@pytest.fixture(scope="session")
def browser_context():
    """Contexto do browser para toda a sessão de testes"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Test Agent)'
        )
        yield context
        context.close()
        browser.close()

@pytest.fixture
def page(browser_context):
    """Nova página para cada teste"""
    page = browser_context.new_page()
    yield page
    page.close()

# Fixtures de LLM

@pytest.fixture
def mock_llm_response():
    """Response padrão do LLM para testes"""
    return {
        "action": "CLICK",
        "selector": "button#submit",
        "reasoning": "Clicking submit button to proceed"
    }

@pytest.fixture
def mock_llm_provider(mock_llm_response):
    """Provider LLM mockado"""
    mock = Mock()
    mock.generate.return_value = str(mock_llm_response)
    mock.is_available.return_value = True
    return mock

# Fixtures de HTML

@pytest.fixture
def sample_html():
    """HTML de exemplo para testes"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Page</h1>
        <form id="test-form">
            <input type="text" id="username" name="username" placeholder="Username">
            <input type="password" id="password" name="password" placeholder="Password">
            <button type="submit" id="submit-btn">Login</button>
        </form>
        <a href="/about" id="about-link">About</a>
        <div id="content">
            <p>This is test content</p>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def sample_complex_html():
    """HTML complexo para testes"""
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/products">Products</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
        <main>
            <section class="products">
                <div class="product-card">
                    <h2>Product 1</h2>
                    <button class="add-to-cart" data-id="1">Add to Cart</button>
                </div>
                <div class="product-card">
                    <h2>Product 2</h2>
                    <button class="add-to-cart" data-id="2">Add to Cart</button>
                </div>
            </section>
        </main>
        <footer>
            <p>&copy; 2024 Test Company</p>
        </footer>
    </body>
    </html>
    """

# Fixtures de Configuração

@pytest.fixture
def test_config():
    """Configuração padrão para testes"""
    return {
        'provider': 'mock',
        'provider_url': 'http://localhost:9999',
        'model': 'test-model',
        'max_steps': 10,
        'headless': True,
        'timeout': 30000
    }

@pytest.fixture
def lmstudio_config():
    """Configuração LM Studio para testes de integração"""
    return {
        'provider': 'lmstudio',
        'provider_url': 'http://localhost:1234',
        'model': 'llama-2-7b-chat',
        'max_steps': 50,
        'headless': True
    }

# Fixtures de Diretórios

@pytest.fixture
def temp_logs_dir(tmp_path):
    """Diretório temporário para logs"""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir

@pytest.fixture
def temp_screenshots_dir(tmp_path):
    """Diretório temporário para screenshots"""
    prints_dir = tmp_path / "prints"
    prints_dir.mkdir()
    return prints_dir

# Fixtures de Estado

@pytest.fixture
def navigation_state():
    """Estado inicial de navegação"""
    return {
        'current_url': 'https://example.com',
        'steps_taken': 0,
        'max_steps': 50,
        'completed': False,
        'error': None,
        'actions_history': []
    }

# Markers customizados

def pytest_configure(config):
    """Configura markers customizados"""
    config.addinivalue_line(
        "markers", "unit: marca teste como unitário"
    )
    config.addinivalue_line(
        "markers", "integration: marca teste como de integração"
    )
    config.addinivalue_line(
        "markers", "e2e: marca teste como end-to-end"
    )
    config.addinivalue_line(
        "markers", "slow: marca teste como lento"
    )
    config.addinivalue_line(
        "markers", "llm: marca teste que requer LLM real"
    )
    config.addinivalue_line(
        "markers", "browser: marca teste que usa browser real"
    )

# Hooks para relatórios

def pytest_report_header(config):
    """Header customizado para relatórios"""
    return [
        "Projeto: Agente de QA Automatizado",
        "Ambiente: Test",
    ]

# Fixtures de Mock HTTP

@pytest.fixture
def mock_http_response():
    """Response HTTP mockado"""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {'status': 'success'}
    mock.text = 'OK'
    return mock

# Fixtures de Dados

@pytest.fixture
def sample_form_data():
    """Dados de formulário para testes"""
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com',
        'phone': '+55 11 99999-9999'
    }

@pytest.fixture
def sample_navigation_instructions():
    """Instruções de navegação para testes"""
    return [
        "Navegue até a página de login",
        "Preencha o formulário de login",
        "Clique no botão de enviar",
        "Verifique se o login foi bem-sucedido"
    ]

# Auto-use fixtures

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset de ambiente antes de cada teste"""
    # Setup
    yield
    # Teardown
    # Limpar qualquer estado global se necessário
    pass
