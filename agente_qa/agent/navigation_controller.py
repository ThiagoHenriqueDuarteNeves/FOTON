"""
Controlador de Navegação - Orquestração da navegação autônoma
Responsável por coordenar a navegação com o agente LLM de forma modular.
"""
from typing import Dict, Any, Optional, List
import logging
import time
import json
import uuid
from datetime import datetime

from .form_handler import FormFieldCapture, LoginHandler
from .llm import LLMClient
from .browser_actions import BrowserActions
from .html_parser import HTMLParser
from .prompt_generator import PromptGenerator
from .validation import ResponseValidator
from .io import LoggingManager


class NavigationController:
    """Controlador principal de navegação com agente LLM"""
    
    def __init__(self, llm_client: LLMClient, browser_actions: BrowserActions):
        self.logger = logging.getLogger(__name__)
        
        # Injeção de dependências
        self.llm_client = llm_client
        self.browser_actions = browser_actions
        self.html_parser = HTMLParser()
        self.prompt_generator = PromptGenerator()
        self.validator = ResponseValidator()
        self.logging_manager = LoggingManager()
        
        # Handlers especializados
        self.form_capture = FormFieldCapture()
        self.login_handler = LoginHandler()
        
        # Estado da navegação
        self.navigation_history = []
        self.execution_id = str(uuid.uuid4())[:8]
    
    def navigate_with_agent(self, url: str, instructions: str, max_steps: int = 30) -> bool:
        """
        Executa navegação autônoma com agente LLM
        
        Args:
            url: URL inicial para navegação
            instructions: Instruções para o agente
            max_steps: Número máximo de passos
            
        Returns:
            bool: True se navegação foi bem sucedida
        """
        self.logger.info(f"🚀 Iniciando navegação autônoma - ID: {self.execution_id}")
        self.logger.info(f"📍 URL: {url}")
        self.logger.info(f"📋 Instruções: {instructions}")
        
        try:
            # Navegação inicial
            if not self._navigate_to_url(url):
                return False
            
            # Loop principal de navegação
            for step in range(max_steps):
                self.logger.info(f"📍 Passo {step + 1}/{max_steps}")
                
                # Extrair dados da página
                page_data = self._extract_page_data()
                if not page_data:
                    self.logger.error("❌ Falha ao extrair dados da página")
                    break
                
                # Verificar se deve executar login automático
                if self._should_execute_auto_login(page_data, instructions):
                    if self._execute_auto_login(page_data, instructions):
                        continue  # Prosseguir para próximo passo após login
                
                # Gerar prompt para LLM
                prompt = self._generate_llm_prompt(page_data, instructions, step)
                
                # Obter resposta do LLM
                llm_response = self._get_llm_response(prompt, step)
                if not llm_response:
                    break
                
                # Validar e normalizar resposta
                normalized_action = self._validate_and_normalize_response(llm_response)
                if not normalized_action:
                    continue
                
                # Executar ação
                success = self._execute_action(normalized_action, step)
                if not success:
                    self.logger.warning(f"⚠️ Ação falhou no passo {step + 1}")
                    continue
                
                # Aguardar estabilização
                self._wait_for_page_stability()
                
                # Verificar condições de parada
                if self._check_completion_conditions(page_data):
                    self.logger.info("✅ Navegação concluída com sucesso!")
                    return True
            
            self.logger.warning(f"⚠️ Navegação atingiu limite de {max_steps} passos")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante navegação: {e}")
            return False
    
    def _navigate_to_url(self, url: str) -> bool:
        """Navega para URL inicial"""
        try:
            self.browser_actions.navigate_to(url)
            self.logger.info(f"✅ Navegação inicial para: {url}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Falha na navegação inicial: {e}")
            return False
    
    def _extract_page_data(self) -> Optional[Dict[str, Any]]:
        """Extrai dados completos da página atual"""
        try:
            page = self.browser_actions.get_current_page()
            
            # HTML parsing
            html_data = self.html_parser.extract_page_elements(page)
            
            # Capturar valores atuais de formulários
            current_values = self.form_capture.capture_current_values(page)
            
            # Capturar screenshot
            screenshot_path = self.logging_manager.save_screenshot(
                page, self.execution_id, len(self.navigation_history)
            )
            
            page_data = {
                **html_data,
                'valores_atuais': current_values,
                'screenshot': screenshot_path,
                'timestamp': datetime.now().isoformat(),
                'step': len(self.navigation_history)
            }
            
            return page_data
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao extrair dados da página: {e}")
            return None
    
    def _should_execute_auto_login(self, page_data: dict, instructions: str) -> bool:
        """Verifica se deve executar login automático"""
        return self.login_handler.should_auto_login(page_data, instructions)
    
    def _execute_auto_login(self, page_data: dict, instructions: str) -> bool:
        """Executa login automático determinístico"""
        credentials = self.login_handler.extract_credentials(instructions)
        if not credentials:
            self.logger.warning("⚠️ Credenciais não encontradas nas instruções")
            return False
        
        cpf, password = credentials
        page = self.browser_actions.get_current_page()
        
        success = self.login_handler.execute_auto_login(page, cpf, password)
        if success:
            self.logger.info("✅ Login automático executado com sucesso")
            self._wait_for_page_stability()
        
        return success
    
    def _generate_llm_prompt(self, page_data: dict, instructions: str, step: int) -> str:
        """Gera prompt para o LLM baseado no contexto atual"""
        pending_fields = self._identify_pending_fields(page_data)
        
        return self.prompt_generator.generate_comprehensive_prompt(
            page_data=page_data,
            instructions=instructions,
            history=self.navigation_history,
            pending_fields=pending_fields,
            step_number=step + 1
        )
    
    def _identify_pending_fields(self, page_data: dict) -> List[str]:
        """Identifica campos ainda não preenchidos"""
        try:
            form_fields = page_data.get('campos_formulario', {})
            current_values = page_data.get('valores_atuais', {})
            pending_fields = []
            
            # Verificar inputs de texto
            for field in form_fields.get('inputs_texto', []):
                field_name = field.get('name', field.get('id', ''))
                selector = f"[name='{field_name}']"
                if selector not in current_values or not current_values[selector].strip():
                    pending_fields.append(f"Campo: {field_name} - {field.get('placeholder', 'campo de texto')}")
            
            # Verificar inputs de senha
            for field in form_fields.get('inputs_senha', []):
                field_name = field.get('name', field.get('id', ''))
                selector = f"[name='{field_name}']"
                if selector not in current_values or not current_values[selector].strip():
                    pending_fields.append(f"Campo: {field_name} - campo de senha")
            
            # Verificar selects
            for field in form_fields.get('selects', []):
                field_name = field.get('name', field.get('id', ''))
                selector = f"[name='{field_name}']"
                if selector not in current_values or not current_values[selector].strip():
                    pending_fields.append(f"Campo: {field_name} - seleção")
            
            return pending_fields
            
        except Exception as e:
            self.logger.debug(f"Erro ao identificar campos pendentes: {e}")
            return []
    
    def _get_llm_response(self, prompt: str, step: int) -> Optional[Dict[str, Any]]:
        """Obtém resposta do LLM e salva logs"""
        try:
            # Salvar payload
            self.logging_manager.save_llm_payload(prompt, self.execution_id, step)
            
            # Obter resposta
            response = self.llm_client.get_completion(prompt)
            
            # Salvar resposta
            self.logging_manager.save_llm_response(response, self.execution_id, step)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter resposta do LLM: {e}")
            return None
    
    def _validate_and_normalize_response(self, llm_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Valida e normaliza resposta do LLM"""
        try:
            # Validar estrutura da resposta
            if not self.validator.validate_llm_response(llm_response):
                return None
            
            # Normalizar formato da ação
            return self.validator.normalize_action_data(llm_response)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao validar resposta: {e}")
            return None
    
    def _execute_action(self, action_data: Dict[str, Any], step: int) -> bool:
        """Executa ação no browser"""
        try:
            # Registrar ação no histórico
            self.navigation_history.append({
                'step': step + 1,
                'action': action_data,
                'timestamp': datetime.now().isoformat()
            })
            
            # Executar ação
            success = self.browser_actions.execute_action(action_data)
            
            if success:
                self.logger.info(f"✅ Ação executada: {action_data.get('tipo', 'desconhecida')}")
            else:
                self.logger.warning(f"⚠️ Falha na execução da ação")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao executar ação: {e}")
            return False
    
    def _wait_for_page_stability(self, timeout: float = 2.0):
        """Aguarda estabilização da página"""
        time.sleep(timeout)
    
    def _check_completion_conditions(self, page_data: dict) -> bool:
        """Verifica condições de conclusão da navegação"""
        try:
            url = page_data.get('pagina', {}).get('url', '').lower()
            title = page_data.get('pagina', {}).get('titulo', '').lower()
            
            # Condições de sucesso
            success_indicators = [
                'customer created' in title,
                'account created' in title,
                'registration successful' in title,
                'success' in url,
                'created' in url
            ]
            
            return any(success_indicators)
            
        except Exception:
            return False
    
    def get_navigation_summary(self) -> Dict[str, Any]:
        """Retorna resumo da navegação"""
        return {
            'execution_id': self.execution_id,
            'total_steps': len(self.navigation_history),
            'history': self.navigation_history,
            'timestamp': datetime.now().isoformat()
        }
