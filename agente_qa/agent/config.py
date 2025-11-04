"""
Módulo de configuração centralizada para variáveis de ambiente e configurações sensíveis.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Centraliza todas as configurações do sistema"""
    
    def __init__(self):
        self._load_environment()
    
    def _load_environment(self):
        """Carrega variáveis de ambiente do arquivo .env se existir"""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
    
    # LLM Configuration
    @property
    def llm_base_url(self) -> str:
        return os.getenv('LLM_BASE_URL', 'http://localhost:1234')
    
    @property
    def llm_timeout(self) -> int:
        return int(os.getenv('LLM_TIMEOUT', '60'))
    
    @property
    def llm_model(self) -> str:
        return os.getenv('LLM_MODEL', 'openai/gpt-oss-20b')
    
    # Ollama Configuration
    @property
    def ollama_base_url(self) -> str:
        return os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    @property
    def ollama_model(self) -> str:
        return os.getenv('OLLAMA_MODEL', 'mistral')
    
    # Browser Configuration
    @property
    def browser_headless(self) -> bool:
        return os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
    
    @property
    def browser_timeout(self) -> int:
        return int(os.getenv('BROWSER_TIMEOUT', '30000'))
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def enable_sensitive_logging(self) -> bool:
        return os.getenv('ENABLE_SENSITIVE_LOGGING', 'false').lower() == 'true'
    
    # Security
    @property
    def enable_auto_login(self) -> bool:
        return os.getenv('ENABLE_AUTO_LOGIN', 'true').lower() == 'true'
    
    @property
    def max_login_attempts(self) -> int:
        return int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))


# Instância global da configuração
config = Config()