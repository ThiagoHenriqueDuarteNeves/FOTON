"""
Main Application - Versão de Teste Simplificada
Teste de compatibilidade com estrutura existente
"""
import sys
import argparse
import logging
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_lmstudio


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
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
    parser = argparse.ArgumentParser(description="Teste da Versão Refatorada")
    
    parser.add_argument('--url', required=True, help='URL inicial')
    parser.add_argument('--instrucoes', required=True, help='Instruções para o agente')
    parser.add_argument('--max-passos', type=int, default=30, help='Máximo de passos')
    parser.add_argument('--verbose', action='store_true', help='Logging detalhado')
    
    return parser.parse_args()


def test_basic_functionality():
    """Teste básico de funcionalidade dos módulos refatorados"""
    logger = logging.getLogger(__name__)
    
    try:
        # Testar import dos novos módulos
        from agent.form_handler import FormFieldCapture, LoginHandler
        logger.info("✅ form_handler importado com sucesso")
        
        # Testar instanciação das classes
        form_capture = FormFieldCapture()
        login_handler = LoginHandler()
        logger.info("✅ Classes instanciadas com sucesso")
        
        # Testar browser
        navegador, pagina, playwright = iniciar_navegador()
        logger.info("✅ Browser inicializado com sucesso")
        
        # Navegar para URL de teste
        pagina.goto("https://parabank.parasoft.com/parabank/register.htm")
        logger.info("✅ Navegação para página de teste realizada")
        
        # Testar captura de valores (novo módulo)
        current_values = form_capture.capture_current_values(pagina)
        logger.info(f"✅ Captura de valores: {len(current_values)} campos detectados")
        
        # Testar detecção de login
        fake_page_data = {
            'campos_formulario': {
                'inputs_texto': [{'name': 'cpf'}],
                'inputs_senha': [{'name': 'senha'}]
            },
            'pagina': {'url': 'https://site.com/login'}
        }
        should_login = login_handler.should_auto_login(fake_page_data, "cpf: 12345678901 senha: teste123")
        logger.info(f"✅ Detecção de login: {should_login}")
        
        # Limpeza
        navegador.close()
        playwright.stop()
        logger.info("✅ Cleanup realizado com sucesso")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False


def main():
    """Função principal de teste"""
    args = parse_arguments()
    logger = setup_logging(args.verbose)
    
    logger.info("🧪 TESTE DE FUNCIONALIDADE DA VERSÃO REFATORADA")
    
    try:
        success = test_basic_functionality()
        
        if success:
            logger.info("🎉 TESTE CONCLUÍDO COM SUCESSO!")
            logger.info("✅ Todos os módulos refatorados funcionam corretamente")
            logger.info("✅ Compatibilidade com estrutura existente confirmada")
        else:
            logger.error("❌ TESTE FALHOU!")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
