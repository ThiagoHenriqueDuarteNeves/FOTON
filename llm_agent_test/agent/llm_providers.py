"""
Interface base para provedores de LLM.
Define o contrato que todos os provedores devem implementar.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class LLMProvider(ABC):
    """Interface base para provedores de LLM"""
    
    @abstractmethod
    def call_llm(self, payload: Dict) -> str:
        """
        Chama o LLM com o payload fornecido
        
        Args:
            payload: Dados para envio ao LLM
            
        Returns:
            str: Resposta do LLM
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Obtém lista de modelos disponíveis
        
        Returns:
            List[str]: Lista de modelos
        """
        pass
    
    @abstractmethod
    def get_loaded_model(self) -> Optional[str]:
        """
        Obtém modelo atualmente carregado
        
        Returns:
            Optional[str]: Nome do modelo ou None
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica se o provedor está disponível
        
        Returns:
            bool: True se disponível
        """
        pass


class LMStudioProvider(LLMProvider):
    """Provedor para LM Studio"""
    
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url
    
    def call_llm(self, payload: Dict) -> str:
        # Implementação específica do LM Studio
        pass
    
    def get_available_models(self) -> List[str]:
        # Implementação específica do LM Studio
        pass
    
    def get_loaded_model(self) -> Optional[str]:
        # Implementação específica do LM Studio
        pass
    
    def is_available(self) -> bool:
        # Verificação de disponibilidade do LM Studio
        pass


class OllamaProvider(LLMProvider):
    """Provedor para Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def call_llm(self, payload: Dict) -> str:
        # Implementação específica do Ollama
        pass
    
    def get_available_models(self) -> List[str]:
        # Implementação específica do Ollama
        pass
    
    def get_loaded_model(self) -> Optional[str]:
        # Implementação específica do Ollama
        pass
    
    def is_available(self) -> bool:
        # Verificação de disponibilidade do Ollama
        pass


class LLMProviderFactory:
    """Factory para criação de provedores LLM"""
    
    _providers = {
        'lmstudio': LMStudioProvider,
        'ollama': OllamaProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> LLMProvider:
        """
        Cria um provedor LLM
        
        Args:
            provider_type: Tipo do provedor ('lmstudio', 'ollama')
            **kwargs: Argumentos específicos do provedor
            
        Returns:
            LLMProvider: Instância do provedor
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Provedor '{provider_type}' não suportado")
        
        provider_class = cls._providers[provider_type]
        return provider_class(**kwargs)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Registra um novo provedor
        
        Args:
            name: Nome do provedor
            provider_class: Classe do provedor
        """
        cls._providers[name] = provider_class