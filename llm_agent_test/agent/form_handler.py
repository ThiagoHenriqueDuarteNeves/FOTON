"""
Módulo Form Handler - Gerenciamento especializado de formulários
Responsável por detectar, capturar valores e gerenciar estado de campos de formulário.
"""
from typing import Dict, Any, Optional
import logging


class FormFieldCapture:
    """Classe responsável por capturar valores atuais de campos de formulário"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def capture_current_values(self, page) -> Dict[str, str]:
        """
        Captura valores atuais de todos os campos de formulário na página
        
        Args:
            page: Instância da página do Playwright
            
        Returns:
            Dict[str, str]: Mapeamento campo -> valor
        """
        try:
            form_values = {}
            
            # Capturar valores de inputs
            form_values.update(self._capture_input_values(page))
            
            # Capturar valores de textareas
            form_values.update(self._capture_textarea_values(page))
            
            # Capturar valores de selects
            form_values.update(self._capture_select_values(page))
            
            return form_values
            
        except Exception as e:
            self.logger.warning(f"Erro ao capturar valores atuais: {e}")
            return {}
    
    def _capture_input_values(self, page) -> Dict[str, str]:
        """Captura valores de elementos input"""
        values = {}
        try:
            input_types = [
                'input[type="text"]', 'input[type="email"]', 'input[type="tel"]',
                'input[type="password"]', 'input[type="number"]', 'input[type="url"]',
                'input:not([type])'
            ]
            
            inputs = page.locator(', '.join(input_types)).all()
            for input_elem in inputs:
                try:
                    value = input_elem.input_value() or ''
                    if value.strip():
                        name = self._get_field_identifier(input_elem)
                        values[f"[name='{name}']"] = value.strip()
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Erro ao capturar inputs: {e}")
            
        return values
    
    def _capture_textarea_values(self, page) -> Dict[str, str]:
        """Captura valores de elementos textarea"""
        values = {}
        try:
            textareas = page.locator('textarea').all()
            for textarea in textareas:
                try:
                    value = textarea.input_value() or ''
                    if value.strip():
                        name = self._get_field_identifier(textarea)
                        values[f"[name='{name}']"] = value.strip()
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Erro ao capturar textareas: {e}")
            
        return values
    
    def _capture_select_values(self, page) -> Dict[str, str]:
        """Captura valores de elementos select"""
        values = {}
        try:
            selects = page.locator('select').all()
            for select in selects:
                try:
                    value = select.input_value() or ''
                    if value.strip():
                        name = self._get_field_identifier(select)
                        values[f"[name='{name}']"] = value.strip()
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Erro ao capturar selects: {e}")
            
        return values
    
    def _get_field_identifier(self, element) -> str:
        """Obtém identificador do campo (name, id ou placeholder)"""
        try:
            return (element.get_attribute('name') or 
                   element.get_attribute('id') or 
                   element.get_attribute('placeholder') or 
                   'campo_sem_nome')
        except Exception:
            return 'campo_sem_nome'


class LoginHandler:
    """Classe responsável por gerenciar login automático determinístico"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def should_auto_login(self, navigation_data: dict, instructions: str) -> bool:
        """
        Determina se deve executar login automático
        
        Args:
            navigation_data: Dados de navegação extraídos
            instructions: Instruções do usuário
            
        Returns:
            bool: True se deve executar login automático
        """
        if not navigation_data or not instructions:
            return False
            
        url = navigation_data.get('pagina', {}).get('url', '').lower()
        has_login_fields = (
            len(navigation_data.get('campos_formulario', {}).get('inputs_texto', [])) > 0 and
            len(navigation_data.get('campos_formulario', {}).get('inputs_senha', [])) > 0
        )
        is_login_page = 'login' in url
        has_login_instruction = any(keyword in instructions.lower() 
                                  for keyword in ['cpf', 'login', 'senha'])
        
        return is_login_page and has_login_fields and has_login_instruction
    
    def extract_credentials(self, instructions: str) -> Optional[tuple]:
        """
        Extrai credenciais das instruções
        
        Args:
            instructions: Instruções do usuário
            
        Returns:
            tuple: (cpf, senha) ou None se não encontrar
        """
        import re
        
        cpf_match = re.search(r'cpf[:\s]*(\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})', 
                             instructions.lower())
        senha_match = re.search(r'senha[:\s]*(\S+)', instructions.lower())
        
        if cpf_match and senha_match:
            cpf = cpf_match.group(1).replace('.', '').replace('-', '')
            senha = senha_match.group(1)
            return cpf, senha
            
        return None
    
    def execute_auto_login(self, page, cpf: str, password: str) -> bool:
        """
        Executa login automático determinístico
        
        Args:
            page: Instância da página do Playwright
            cpf: CPF para login
            password: Senha para login
            
        Returns:
            bool: True se login foi executado com sucesso
        """
        selectors = self._get_login_selectors()
        
        # Preencher CPF
        if not self._fill_field(page, selectors['cpf'], cpf, "CPF"):
            return False
            
        # Preencher senha
        if not self._fill_field(page, selectors['password'], password, "Senha"):
            return False
            
        # Executar submit
        return self._submit_form(page, selectors['submit'])
    
    def _get_login_selectors(self) -> Dict[str, list]:
        """Retorna seletores robustos para login"""
        return {
            'cpf': [
                'form input[formcontrolname=cpf]',
                'form input[name=cpf]',
                'form input[placeholder*="CPF" i]',
                'form input#login',
                'form input[type=tel]',
                'form input[type=text]:visible'
            ],
            'password': [
                'form input[formcontrolname=senha]',
                'form input[name=senha]',
                'form input[type=password]:visible'
            ],
            'submit': [
                'form button[type=submit]:visible',
                'form [role="button"]:has-text("Entrar"):visible',
                'form button:has-text("Entrar"):visible',
                'form input[type=submit]:visible'
            ]
        }
    
    def _fill_field(self, page, selectors: list, value: str, field_name: str) -> bool:
        """Preenche campo usando lista de seletores"""
        for selector in selectors:
            try:
                if page.locator(selector).count() > 0:
                    current_value = page.locator(selector).first.input_value()
                    if current_value != value:
                        page.locator(selector).first.wait_for(state="visible", timeout=3000)
                        page.locator(selector).first.clear()
                        page.locator(selector).first.fill(value)
                        self.logger.info(f"{field_name} preenchido com: {selector}")
                    else:
                        self.logger.info(f"{field_name} já preenchido em: {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"Falhou seletor {field_name} {selector}: {e}")
                continue
        return False
    
    def _submit_form(self, page, selectors: list) -> bool:
        """Executa submit do formulário"""
        for selector in selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    self.logger.info(f"Submit executado com: {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"Falhou submit {selector}: {e}")
                continue
                
        # Fallbacks
        return self._try_fallback_submit(page)
    
    def _try_fallback_submit(self, page) -> bool:
        """Tenta fallbacks para submit"""
        try:
            # Fallback 1: Enter no campo senha
            password_selectors = self._get_login_selectors()['password']
            for selector in password_selectors:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.press("Enter")
                    self.logger.info("Fallback Enter executado")
                    return True
        except Exception:
            pass
            
        try:
            # Fallback 2: Submit do formulário via JS
            page.evaluate("document.querySelector('form')?.requestSubmit?.()")
            self.logger.info("Fallback form submit executado")
            return True
        except Exception:
            pass
            
        return False
