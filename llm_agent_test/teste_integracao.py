"""
Teste de Integração - Validação da refatoração com funcionalidade completa
Testa se os módulos refatorados podem executar o mesmo fluxo do main.py original
"""
import sys
import argparse
import logging
import time
import json
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Imports da estrutura existente
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_lmstudio
from agent.prompt_generator import extrair_elementos_otimizados_llm, gerar_prompt_autonomo_completo
from agent.browser_actions import executar_acao, limpar_estado_campos
from agent.validation import validar_resposta_llm
from agent.io import salvar_screenshot, salvar_resposta_modelo, salvar_payload_log

# Imports dos módulos refatorados
from agent.form_handler import FormFieldCapture, LoginHandler


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    return logger


def test_integrated_navigation(url: str, instrucoes: str, max_passos: int = 15):
    """
    Testa navegação integrada usando módulos refatorados + estrutura existente
    """
    logger = logging.getLogger(__name__)
    
    # Inicializar componentes refatorados
    form_capture = FormFieldCapture()
    login_handler = LoginHandler()
    
    # Inicializar browser
    navegador, pagina, playwright = iniciar_navegador()
    limpar_estado_campos()  # Estado limpo
    
    historico_navegacao = []
    
    try:
        logger.info(f"🚀 Iniciando teste integrado")
        logger.info(f"📍 URL: {url}")
        logger.info(f"📋 Instruções: {instrucoes}")
        
        # Navegar para URL
        pagina.goto(url)
        logger.info("✅ Navegação inicial realizada")
        
        for passo in range(max_passos):
            logger.info(f"📍 Passo {passo + 1}/{max_passos}")
            
            # 1. EXTRAIR DADOS DA PÁGINA (estrutura existente)
            dados_navegacao = extrair_elementos_otimizados_llm(pagina)
            if not dados_navegacao:
                logger.error("❌ Falha ao extrair dados da página")
                break
                
            # 2. CAPTURAR VALORES ATUAIS (módulo refatorado)
            valores_atuais = form_capture.capture_current_values(pagina)
            dados_navegacao['valores_atuais'] = valores_atuais
            logger.info(f"🔍 Campos preenchidos detectados: {len(valores_atuais)}")
            
            # 3. VERIFICAR LOGIN AUTOMÁTICO (módulo refatorado)
            if login_handler.should_auto_login(dados_navegacao, instrucoes):
                logger.info("🔐 Tentando login automático...")
                credentials = login_handler.extract_credentials(instrucoes)
                if credentials:
                    cpf, senha = credentials
                    if login_handler.execute_auto_login(pagina, cpf, senha):
                        logger.info("✅ Login automático executado")
                        time.sleep(3)
                        continue
            
            # 4. GERAR PROMPT (estrutura existente)
            campos_pendentes = _identificar_campos_pendentes(dados_navegacao, valores_atuais)
            
            # Gerar screenshot
            screenshot_path = f"prints/teste_integrado_passo_{passo+1}.png"
            salvar_screenshot(pagina, passo + 1)
            
            # Extrair HTML para prompt
            html_content = dados_navegacao.get('html', '')
            
            prompt = gerar_prompt_autonomo_completo(
                html_content=html_content,
                screenshot_path=screenshot_path,
                instrucoes_customizadas=instrucoes,
                historico_acoes=historico_navegacao,
                pagina=pagina
            )
            
            # 5. OBTER RESPOSTA DO LLM (estrutura existente)
            logger.info("🧠 Consultando LLM...")
            salvar_payload_log(prompt, f"teste_integrado_passo_{passo+1}")
            
            resposta_llm = chamar_llm_lmstudio(prompt)
            if not resposta_llm:
                logger.error("❌ Falha na resposta do LLM")
                break
                
            salvar_resposta_modelo(resposta_llm, resposta_llm, passo + 1, "google/gemma-3n-e4b")
            
            # 6. VALIDAR RESPOSTA (estrutura existente)
            if not validar_resposta_llm(resposta_llm):
                logger.warning("⚠️ Resposta LLM inválida")
                continue
            
            # 7. EXECUTAR AÇÃO (estrutura existente)
            sucesso, _ = executar_acao(pagina, resposta_llm)
            
            if sucesso:
                logger.info("✅ Ação executada com sucesso")
                
                # Adicionar ao histórico
                historico_navegacao.append({
                    'passo': passo + 1,
                    'acao': resposta_llm,
                    'dados_pagina': dados_navegacao
                })
                
                # Screenshot
                salvar_screenshot(pagina, f"teste_integrado_passo_{passo+1}")
                
                # Aguardar
                time.sleep(2)
                
                # Verificar condições de parada
                if _verificar_conclusao(pagina):
                    logger.info("🎉 NAVEGAÇÃO CONCLUÍDA COM SUCESSO!")
                    return True
                    
            else:
                logger.warning("⚠️ Ação falhou")
                continue
        
        logger.warning(f"⚠️ Atingiu limite de {max_passos} passos")
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        return False
        
    finally:
        navegador.close()
        playwright.stop()


def _identificar_campos_pendentes(dados_navegacao: dict, valores_atuais: dict) -> list:
    """Identifica campos ainda não preenchidos"""
    pendentes = []
    
    try:
        form_fields = dados_navegacao.get('campos_formulario', {})
        
        # Verificar inputs de texto
        for field in form_fields.get('inputs_texto', []):
            field_name = field.get('name', field.get('id', ''))
            selector = f"[name='{field_name}']"
            if selector not in valores_atuais or not valores_atuais[selector].strip():
                pendentes.append(f"Campo: {field_name} - {field.get('placeholder', 'campo de texto')}")
        
        # Verificar inputs de senha
        for field in form_fields.get('inputs_senha', []):
            field_name = field.get('name', field.get('id', ''))
            selector = f"[name='{field_name}']"
            if selector not in valores_atuais or not valores_atuais[selector].strip():
                pendentes.append(f"Campo: {field_name} - campo de senha")
        
        # Verificar selects
        for field in form_fields.get('selects', []):
            field_name = field.get('name', field.get('id', ''))
            selector = f"[name='{field_name}']"
            if selector not in valores_atuais or not valores_atuais[selector].strip():
                pendentes.append(f"Campo: {field_name} - seleção")
    
    except Exception as e:
        logging.debug(f"Erro ao identificar pendentes: {e}")
    
    return pendentes


def _verificar_conclusao(pagina) -> bool:
    """Verifica se a navegação foi concluída"""
    try:
        url = pagina.url.lower()
        title = pagina.title().lower()
        
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


def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description="Teste de Integração Refatoração")
    
    parser.add_argument('--url', required=True, help='URL inicial')
    parser.add_argument('--instrucoes', required=True, help='Instruções para o agente')
    parser.add_argument('--max-passos', type=int, default=15, help='Máximo de passos')
    parser.add_argument('--verbose', action='store_true', help='Logging detalhado')
    
    return parser.parse_args()


def main():
    """Função principal de teste integrado"""
    args = parse_arguments()
    logger = setup_logging(args.verbose)
    
    logger.info("🧪 TESTE DE INTEGRAÇÃO - REFATORAÇÃO + FUNCIONALIDADE ORIGINAL")
    
    try:
        success = test_integrated_navigation(
            url=args.url,
            instrucoes=args.instrucoes,
            max_passos=args.max_passos
        )
        
        if success:
            logger.info("🎉 TESTE DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO!")
            logger.info("✅ Módulos refatorados integrados corretamente")
            logger.info("✅ Funcionalidade original preservada")
        else:
            logger.error("❌ TESTE DE INTEGRAÇÃO FALHOU")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
