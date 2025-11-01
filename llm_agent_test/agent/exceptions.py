"""
Módulo de exceções customizadas do sistema.
Define todas as exceções específicas do domínio.
"""


class WebAutomationError(Exception):
    """Exceção base para erros de automação web"""
    pass


class LLMConnectionError(WebAutomationError):
    """Erro de conexão com o LLM"""
    pass


class BrowserError(WebAutomationError):
    """Erro relacionado ao navegador"""
    pass


class ElementNotFoundError(BrowserError):
    """Elemento não encontrado na página"""
    pass


class TimeoutError(WebAutomationError):
    """Timeout em operação"""
    pass


class ValidationError(WebAutomationError):
    """Erro de validação de dados"""
    pass


class ConfigurationError(WebAutomationError):
    """Erro de configuração do sistema"""
    pass


class AuthenticationError(WebAutomationError):
    """Erro de autenticação/login"""
    pass