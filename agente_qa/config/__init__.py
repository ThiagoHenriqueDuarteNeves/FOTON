# config/__init__.py
"""
Módulo de configuração centralizada.

Uso:
    from config import config
    
    print(config.llm.PROVIDER)
    print(config.backend.PORT)
"""

from .settings import (
    config,
    Config,
    LLMConfig,
    NavigationConfig,
    BackendConfig,
    FrontendConfig,
    LogConfig,
    ScreenshotConfig,
    CacheConfig,
)

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
