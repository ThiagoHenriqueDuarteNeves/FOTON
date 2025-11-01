"""
Módulo de constantes do sistema.
Centraliza todos os valores constantes utilizados no projeto.
"""

# Timeouts (em segundos)
DEFAULT_TIMEOUT = 30
LLM_TIMEOUT = 60
BROWSER_TIMEOUT = 30

# Limites do sistema
MAX_STEPS = 100
MAX_LOGIN_ATTEMPTS = 3
MAX_RETRY_ATTEMPTS = 3

# Seletores CSS comuns
COMMON_SELECTORS = {
    'login_fields': [
        'input[name="username"]',
        'input[name="login"]', 
        'input[name="email"]',
        'input[name="cpf"]'
    ],
    'password_fields': [
        'input[type="password"]',
        'input[name="password"]',
        'input[name="senha"]'
    ],
    'submit_buttons': [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:contains("Login")',
        'button:contains("Entrar")'
    ]
}

# Mensagens de erro padronizadas
ERROR_MESSAGES = {
    'llm_connection': 'Falha na conexão com o LLM',
    'browser_timeout': 'Timeout na operação do navegador',
    'invalid_selector': 'Seletor CSS inválido',
    'element_not_found': 'Elemento não encontrado na página',
    'max_steps_reached': 'Número máximo de passos atingido'
}

# Configurações de logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configurações do navegador
BROWSER_ARGS = [
    "--start-maximized",
    "--disable-infobars", 
    "--disable-notifications",
    "--force-device-scale-factor=1",
    "--window-size=1920,1080"
]

# User agents
USER_AGENTS = {
    'chrome': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    'firefox': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"
}