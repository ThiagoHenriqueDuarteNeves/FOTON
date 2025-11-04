# config/settings.py
"""
Configurações centralizadas do projeto.
Carrega variáveis de ambiente e define constantes.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = BASE_DIR / "agent"
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = BASE_DIR / "prints"
TESTS_DIR = BASE_DIR / "tests"

# Criar diretórios se não existirem
LOGS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# === Configurações de LLM ===

class LLMConfig:
    """Configurações de LLM"""
    
    PROVIDER: str = os.getenv("LLM_PROVIDER", "lmstudio")
    
    # URLs dos provedores
    LMSTUDIO_URL: str = os.getenv("LMSTUDIO_URL", "http://localhost:1234")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    EXTERNAL_API_URL: str = os.getenv("EXTERNAL_API_URL", "https://api.openai.com/v1")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Modelo padrão
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-2-7b-chat")
    
    # Timeout
    TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))

# === Configurações de Navegação ===

class NavigationConfig:
    """Configurações de navegação"""
    
    MAX_STEPS: int = int(os.getenv("MAX_STEPS", "50"))
    ACTION_TIMEOUT: int = int(os.getenv("ACTION_TIMEOUT", "30000"))
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    BROWSER_TYPE: str = os.getenv("BROWSER_TYPE", "chromium")
    USER_AGENT: Optional[str] = os.getenv("USER_AGENT")

# === Configurações do Backend ===

class BackendConfig:
    """Configurações do backend FastAPI"""
    
    HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    AUTO_RELOAD: bool = os.getenv("AUTO_RELOAD", "true").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # Segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))

# === Configurações do Frontend ===

class FrontendConfig:
    """Configurações do frontend"""
    
    PORT: int = int(os.getenv("FRONTEND_PORT", "3000"))

# === Configurações de Logging ===

class LogConfig:
    """Configurações de logging"""
    
    LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DIR: Path = Path(os.getenv("LOG_DIR", str(LOGS_DIR)))
    FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    ENABLE_SENSITIVE_LOGGING: bool = os.getenv(
        "ENABLE_SENSITIVE_LOGGING", "false"
    ).lower() == "true"

# === Configurações de Screenshots ===

class ScreenshotConfig:
    """Configurações de screenshots"""
    
    DIR: Path = Path(os.getenv("SCREENSHOTS_DIR", str(SCREENSHOTS_DIR)))
    FORMAT: str = os.getenv("SCREENSHOT_FORMAT", "png")
    QUALITY: int = int(os.getenv("SCREENSHOT_QUALITY", "90"))

# === Configurações de Cache ===

class CacheConfig:
    """Configurações de cache"""
    
    ENABLE_LLM_CACHE: bool = os.getenv("ENABLE_LLM_CACHE", "false").lower() == "true"
    TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hora

# === Configurações Gerais ===

class Config:
    """Configurações gerais do projeto"""
    
    llm = LLMConfig()
    navigation = NavigationConfig()
    backend = BackendConfig()
    frontend = FrontendConfig()
    log = LogConfig()
    screenshot = ScreenshotConfig()
    cache = CacheConfig()
    
    # Diretórios
    BASE_DIR = BASE_DIR
    LOGS_DIR = LOGS_DIR
    SCREENSHOTS_DIR = SCREENSHOTS_DIR

# Instância global
config = Config()

# Exportações
__all__ = [
    "config",
    "Config",
    "LLMConfig",
    "NavigationConfig",
    "BackendConfig",
    "FrontendConfig",
    "LogConfig",
    "ScreenshotConfig",
    "CacheConfig",
]
