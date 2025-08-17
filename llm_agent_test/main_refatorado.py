"""
Main Application - Ponto de entrada refatorado e simplificado
Responsável apenas por configuração inicial e orquestração de alto nível.
"""
import sys
import argparse
import logging
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.browser import iniciar_navegador
from agent.llm import LLMClient
from agent.browser_actions import executar_acao_no_navegador
from agent.navigation_controller import NavigationController
from agent.io import salvar_screenshot, salvar_resposta_modelo, salvar_prompt_llm


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger raiz
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    return logger


def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description="Agente de Navegação Web Autônomo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Navegação básica
  python main.py --url "https://parabank.parasoft.com/parabank/register.htm" 
                 --instrucoes "Preencher formulário de cadastro"

  # Com credenciais de login
  python main.py --url "https://site.com/login" 
                 --instrucoes "Fazer login com CPF: 12345678901 senha: minhasenha"

  # Modo verboso
  python main.py --url "https://exemplo.com" --instrucoes "..." --verbose

  # Limite personalizado de passos
  python main.py --url "https://exemplo.com" --instrucoes "..." --max-passos 50
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='URL inicial para navegação'
    )
    
    parser.add_argument(
        '--instrucoes',
        required=True,
        help='Instruções detalhadas para o agente executar'
    )
    
    parser.add_argument(
        '--max-passos',
        type=int,
        default=30,
        help='Número máximo de passos de navegação (padrão: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Ativar logging detalhado (debug)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Executar browser em modo headless'
    )
    
    return parser.parse_args()


class AgentApplication:
    """Aplicação principal do agente de navegação"""
    
    def __init__(self, headless: bool = False, verbose: bool = False):
        self.logger = setup_logging(verbose)
        self.logger.info("🤖 Inicializando Agente de Navegação Web")
        
        # Inicializar componentes
        self.logging_manager = LoggingManager()
        self.browser_manager = BrowserManager()
        self.llm_client = LLMClient()
        
        # Configurar browser
        self.browser_actions = None
        self.navigation_controller = None
        self.headless = headless
    
    def initialize_browser(self):
        """Inicializa browser e componentes dependentes"""
        try:
            # Inicializar browser
            page = self.browser_manager.get_page(headless=self.headless)
            
            # Inicializar ações do browser
            self.browser_actions = BrowserActions(page)
            
            # Inicializar controlador de navegação
            self.navigation_controller = NavigationController(
                llm_client=self.llm_client,
                browser_actions=self.browser_actions
            )
            
            self.logger.info("✅ Browser inicializado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar browser: {e}")
            return False
    
    def run_navigation(self, url: str, instructions: str, max_steps: int = 30) -> bool:
        """
        Executa navegação autônoma
        
        Args:
            url: URL inicial
            instructions: Instruções para o agente
            max_steps: Máximo de passos de navegação
            
        Returns:
            bool: True se navegação foi bem sucedida
        """
        if not self.navigation_controller:
            self.logger.error("❌ Controlador de navegação não inicializado")
            return False
        
        try:
            # Executar navegação
            success = self.navigation_controller.navigate_with_agent(
                url=url,
                instructions=instructions,
                max_steps=max_steps
            )
            
            # Obter resumo
            summary = self.navigation_controller.get_navigation_summary()
            
            # Log final
            if success:
                self.logger.info("🎉 Navegação concluída com SUCESSO!")
                self.logger.info(f"📊 Total de passos: {summary['total_steps']}")
            else:
                self.logger.warning("⚠️ Navegação finalizada sem sucesso completo")
                self.logger.info(f"📊 Passos executados: {summary['total_steps']}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante navegação: {e}")
            return False
    
    def cleanup(self):
        """Limpeza de recursos"""
        try:
            if self.browser_manager:
                self.browser_manager.close()
                self.logger.info("🧹 Browser fechado com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Erro durante limpeza: {e}")


def main():
    """Função principal"""
    # Parse argumentos
    args = parse_arguments()
    
    # Criar aplicação
    app = AgentApplication(
        headless=args.headless,
        verbose=args.verbose
    )
    
    try:
        # Inicializar browser
        if not app.initialize_browser():
            sys.exit(1)
        
        # Executar navegação
        success = app.run_navigation(
            url=args.url,
            instructions=args.instrucoes,
            max_steps=args.max_passos
        )
        
        # Exit code baseado no sucesso
        exit_code = 0 if success else 1
        
    except KeyboardInterrupt:
        app.logger.info("⚠️ Execução interrompida pelo usuário")
        exit_code = 1
        
    except Exception as e:
        app.logger.error(f"❌ Erro inesperado: {e}")
        exit_code = 1
        
    finally:
        # Limpeza
        app.cleanup()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
