"""
Módulo de Ações do Navegador - Execução de ações no Playwright
Centraliza todas as operações de interação com elementos da página.

Fluxo de Execução:
- Recebe comando JSON do LLM
- Valida seletor na página
- Executa ação específica (click, fill, etc.)
- Gerencia estado de campos preenchidos
- Trata erros e retry automático
"""
import logging
import time
from typing import Dict, Any, Tuple, Optional
from .validation import validar_resposta_llm, validar_seletor_existente


# Estado global para controle de campos preenchidos
_campos_preenchidos = set()


def limpar_estado_campos():
    """
    Limpa o estado de campos preenchidos.
    
    Fluxo: Chamado no início de cada nova execução
    """
    global _campos_preenchidos
    _campos_preenchidos.clear()
    logging.info("Estado de campos preenchidos limpo")


def adicionar_campo_preenchido(seletor: str):
    """
    Marca um campo como preenchido.
    
    Args:
        seletor (str): Seletor do campo preenchido
    
    Fluxo: Chamado após preencher campo com sucesso
    """
    global _campos_preenchidos
    _campos_preenchidos.add(seletor)
    logging.info(f"Campo marcado como preenchido: {seletor}")


def campo_ja_preenchido(seletor: str) -> bool:
    """
    Verifica se um campo já foi preenchido.
    
    Args:
        seletor (str): Seletor do campo
    
    Returns:
        bool: True se campo já foi preenchido
    
    Fluxo: Chamado antes de preencher campo para evitar duplicação
    """
    global _campos_preenchidos
    return seletor in _campos_preenchidos


def executar_acao(pagina, resposta_llm: str) -> Tuple[bool, str]:
    """
    Executa uma ação baseada na resposta do LLM.
    
    Args:
        pagina: Objeto da página do Playwright
        resposta_llm (str): Resposta JSON do LLM
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    
    Fluxo: Função principal para executar ações validadas
    """
    try:
        # Validar formato JSON da resposta
        valida, dados_json, motivo = validar_resposta_llm(resposta_llm)
        if not valida:
            return False, f"Resposta inválida: {motivo}"
        
        acao = dados_json.get("action", "").lower()
        seletor = dados_json.get("selector", "")
        valor = dados_json.get("value", "")
        
        logging.info(f"Executando ação: {acao} no seletor: {seletor}")
        
        # Executar ação específica (sem verificação prévia - deixar para as funções robustas)
        if acao == "click":
            return _executar_click(pagina, seletor)
        elif acao == "fill":
            return _executar_fill(pagina, seletor, valor)
        elif acao == "submit":
            # Tentativa de submeter: clicar no botão ou submeter o form
            try:
                # Preferir clicar no seletor se existir
                if _elemento_existe(pagina, seletor):
                    return _executar_click(pagina, seletor)
                # Tentar submeter o formulário que contém o seletor (se seletor for um campo)
                try:
                    pagina.evaluate("(sel) => { const el = document.querySelector(sel); el?.closest('form')?.requestSubmit?.(); }", seletor)
                    return True, "Form submit executado via requestSubmit"
                except Exception as e:
                    logging.warning(f"Tentativa de submit via form falhou: {e}")
                    return False, f"Não foi possível submeter o formulário: {e}"
            except Exception as e:
                logging.error(f"Erro no submit: {e}")
                return False, f"Erro no submit: {e}"
        elif acao == "select":
            return _executar_select(pagina, seletor, valor)
        elif acao == "wait":
            return _executar_wait(pagina, valor)
        elif acao == "scroll":
            return _executar_scroll(pagina, seletor)
        elif acao == "hover":
            return _executar_hover(pagina, seletor)
        elif acao == "press":
            return _executar_press(pagina, valor)
        elif acao == "type":
            return _executar_type(pagina, seletor, valor)
        elif acao == "clear":
            return _executar_clear(pagina, seletor)
        else:
            return False, f"Ação não suportada: {acao}"
            
    except Exception as e:
        logging.error(f"Erro ao executar ação: {e}")
        return False, f"Erro na execução: {e}"


def _elemento_existe(pagina, seletor: str) -> bool:
    """
    Verifica se elemento existe na página.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor CSS
    
    Returns:
        bool: True se elemento existe
    """
    try:
        return pagina.locator(seletor).count() > 0
    except Exception as e:
        logging.warning(f"Erro ao verificar existência do elemento {seletor}: {e}")
        return False


def _executar_click(pagina, seletor: str) -> Tuple[bool, str]:
    """
    Executa clique em elemento.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do elemento
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        elemento = pagina.locator(seletor)
        
        # Aguardar elemento ficar visível
        elemento.wait_for(state="visible", timeout=5000)
        
        # Scroll até elemento se necessário
        elemento.scroll_into_view_if_needed()
        
        # Clique
        elemento.click(timeout=5000)
        
        logging.info(f"Clique executado com sucesso: {seletor}")
        print(f"[🎯] Clique: ✅ Elemento {seletor} clicado")
        return True, "Clique executado"
        
    except Exception as e:
        erro_str = str(e)
        logging.error(f"Erro ao clicar em {seletor}: {e}")
        
        # Detectar se o erro foi por elemento oculto/invisível
        if "hidden" in erro_str.lower() or "not visible" in erro_str.lower() or "detached" in erro_str.lower():
            return False, f"ELEMENTO_INVISIVEL: {seletor} existe mas está oculto na página. Tente outro seletor alternativo!"
        
        return False, f"Erro no clique: {e}"


def _executar_fill(pagina, seletor: str, valor: str) -> Tuple[bool, str]:
    """
    Preenche campo com valor usando abordagem robusta.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do campo
        valor (str): Valor para preencher
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        if not valor:
            return False, "Valor vazio para preenchimento"
        
        # Verificar se campo já foi preenchido
        if campo_ja_preenchido(seletor):
            logging.info(f"Campo já preenchido, pulando: {seletor}")
            return True, "Campo já preenchido anteriormente"
        
        print(f"[📝] Tentando localizar elemento para fill: {seletor}")
        
        # Tentar múltiplos seletores se o original falhar
        seletores_alternativos = [seletor]
        
        # Se o seletor tem pontos, tentar versão escapada
        if '#' in seletor and '.' in seletor and '\\' not in seletor:
            seletor_escapado = seletor.replace('.', '\\.')
            seletores_alternativos.append(seletor_escapado)
            print(f"[📝] Tentando também versão escapada: {seletor_escapado}")
        
        elemento = None
        seletor_usado = None
        
        # Tentar cada seletor
        for sel in seletores_alternativos:
            try:
                elemento = pagina.locator(sel)
                if elemento.count() > 0:
                    seletor_usado = sel
                    print(f"[📝] ✅ Elemento encontrado com seletor: {sel}")
                    break
            except Exception:
                continue
        
        if not elemento or not seletor_usado:
            return False, f"Elemento não encontrado com nenhum seletor: {seletores_alternativos}"
        
        # Aguardar elemento ficar visível e editável
        elemento.wait_for(state="visible", timeout=5000)
        
        # Scroll até elemento se necessário
        elemento.scroll_into_view_if_needed()
        
        # PASSO 1: Clicar para focar 
        print(f"[📝] 1. Clicando para focar o campo...")
        elemento.click()
        
        # PASSO 2: Limpar campo primeiro
        print(f"[📝] 2. Limpando campo existente...")
        elemento.clear()
        
        # PASSO 3: Preencher com valor
        print(f"[📝] 3. Preenchendo com '{valor}'...")
        elemento.fill(valor)
        
        # PASSO 4: Verificar se foi preenchido corretamente
        valor_atual = elemento.input_value()
        if valor_atual == valor:
            adicionar_campo_preenchido(seletor)
            logging.info(f"Campo preenchido com sucesso: {seletor_usado} = '{valor}'")
            print(f"[📝] Campo preenchido: ✅ '{valor}' inserido em {seletor_usado}")
            return True, f"Campo preenchido com '{valor}'"
        else:
            logging.warning(f"Valor não coincide após preenchimento: esperado='{valor}', atual='{valor_atual}'")
            print(f"[📝] ⚠️  Verificação: Esperado '{valor}', obtido '{valor_atual}'")
            return False, "Valor não foi preenchido corretamente"
        
    except Exception as e:
        logging.error(f"Erro ao preencher campo {seletor}: {e}")
        print(f"[📝] ❌ Erro no preenchimento: {e}")
        return False, f"Erro no preenchimento: {e}"


def _executar_select(pagina, seletor: str, valor: str) -> Tuple[bool, str]:
    """
    Seleciona opção em elemento select.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do select
        valor (str): Valor ou texto da opção
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        if not valor:
            return False, "Valor vazio para seleção"
        
        elemento = pagina.locator(seletor)
        
        # Aguardar elemento ficar visível
        elemento.wait_for(state="visible", timeout=5000)
        
        # Scroll até elemento se necessário
        elemento.scroll_into_view_if_needed()
        
        # Tentar selecionar por valor, texto ou index
        try:
            # Método 1: por valor
            elemento.select_option(value=valor)
        except:
            try:
                # Método 2: por texto
                elemento.select_option(label=valor)
            except:
                # Método 3: por índice se valor é numérico
                if valor.isdigit():
                    elemento.select_option(index=int(valor))
                else:
                    raise Exception(f"Não foi possível selecionar opção: {valor}")
        
        logging.info(f"Opção selecionada com sucesso: {seletor} = '{valor}'")
        return True, f"Opção '{valor}' selecionada"
        
    except Exception as e:
        logging.error(f"Erro ao selecionar em {seletor}: {e}")
        return False, f"Erro na seleção: {e}"


def _executar_wait(pagina, valor: str) -> Tuple[bool, str]:
    """
    Aguarda tempo especificado.
    
    Args:
        pagina: Página do Playwright
        valor (str): Tempo em segundos
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        tempo = float(valor) if valor else 1.0
        tempo = min(tempo, 10.0)  # Máximo 10 segundos
        
        time.sleep(tempo)
        
        logging.info(f"Aguardou {tempo} segundos")
        return True, f"Aguardou {tempo}s"
        
    except Exception as e:
        logging.error(f"Erro ao aguardar: {e}")
        return False, f"Erro na espera: {e}"


def _executar_scroll(pagina, seletor: str) -> Tuple[bool, str]:
    """
    Rola página até elemento.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do elemento
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        elemento = pagina.locator(seletor)
        elemento.scroll_into_view_if_needed()
        
        logging.info(f"Scroll executado para: {seletor}")
        return True, "Scroll executado"
        
    except Exception as e:
        logging.error(f"Erro ao fazer scroll: {e}")
        return False, f"Erro no scroll: {e}"


def _executar_hover(pagina, seletor: str) -> Tuple[bool, str]:
    """
    Executa hover sobre elemento.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do elemento
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        elemento = pagina.locator(seletor)
        elemento.hover()
        
        logging.info(f"Hover executado em: {seletor}")
        return True, "Hover executado"
        
    except Exception as e:
        logging.error(f"Erro ao fazer hover: {e}")
        return False, f"Erro no hover: {e}"


def _executar_press(pagina, valor: str) -> Tuple[bool, str]:
    """
    Pressiona tecla especificada.
    
    Args:
        pagina: Página do Playwright
        valor (str): Tecla para pressionar (Enter, Tab, etc.)
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        if not valor:
            return False, "Tecla não especificada"
        
        pagina.keyboard.press(valor)
        
        logging.info(f"Tecla pressionada: {valor}")
        return True, f"Tecla '{valor}' pressionada"
        
    except Exception as e:
        logging.error(f"Erro ao pressionar tecla: {e}")
        return False, f"Erro ao pressionar tecla: {e}"


def _executar_type(pagina, seletor: str, valor: str) -> Tuple[bool, str]:
    """
    Digita texto em elemento com abordagem robusta.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do elemento
        valor (str): Texto para digitar
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        if not valor:
            return False, "Valor vazio para digitação"
        
        print(f"[📝] Tentando localizar elemento: {seletor}")
        
        # Tentar múltiplos seletores se o original falhar
        seletores_alternativos = [seletor]
        
        # Se o seletor tem pontos, tentar versão escapada
        if '#' in seletor and '.' in seletor and '\\' not in seletor:
            seletor_escapado = seletor.replace('.', '\\.')
            seletores_alternativos.append(seletor_escapado)
            print(f"[📝] Tentando também versão escapada: {seletor_escapado}")
        
        elemento = None
        seletor_usado = None
        
        # Tentar cada seletor
        for sel in seletores_alternativos:
            try:
                elemento = pagina.locator(sel)
                if elemento.count() > 0:
                    seletor_usado = sel
                    print(f"[📝] ✅ Elemento encontrado com seletor: {sel}")
                    break
            except Exception:
                continue
        
        if not elemento or not seletor_usado:
            return False, f"Elemento não encontrado com nenhum seletor: {seletores_alternativos}"
        
        # Aguardar elemento ficar visível
        elemento.wait_for(state="visible", timeout=5000)
        
        # Scroll para elemento se necessário
        elemento.scroll_into_view_if_needed()
        
        # PASSO 1: Clicar para focar (sua sugestão!)
        print(f"[📝] 1. Clicando para focar o campo...")
        elemento.click()
        
        # PASSO 2: Limpar campo existente
        print(f"[📝] 2. Limpando campo existente...")
        elemento.clear()
        
        # PASSO 3: Digitar o novo valor
        print(f"[📝] 3. Digitando '{valor}'...")
        elemento.type(valor, delay=50)  # Pequeno delay entre teclas
        
        # PASSO 4: Verificar se foi preenchido
        try:
            valor_atual = elemento.input_value()
            if valor_atual == valor:
                print(f"[📝] ✅ Verificação: Campo preenchido corretamente com '{valor}'")
            else:
                print(f"[📝] ⚠️  Verificação: Esperado '{valor}', obtido '{valor_atual}'")
        except Exception:
            print(f"[📝] ⚠️  Não foi possível verificar o valor preenchido")
        
        logging.info(f"Texto digitado em {seletor_usado}: '{valor}'")
        print(f"[📝] Digitação: ✅ '{valor}' inserido em {seletor_usado}")
        return True, f"Texto '{valor}' digitado com sucesso"
        
    except Exception as e:
        logging.error(f"Erro ao digitar em {seletor}: {e}")
        print(f"[📝] ❌ Erro na digitação: {e}")
        return False, f"Erro na digitação: {e}"


def _executar_clear(pagina, seletor: str) -> Tuple[bool, str]:
    """
    Limpa conteúdo de elemento.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do elemento
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        elemento = pagina.locator(seletor)
        
        # Aguardar elemento ficar visível
        elemento.wait_for(state="visible", timeout=5000)
        
        # Limpar campo
        elemento.clear()
        
        logging.info(f"Campo limpo: {seletor}")
        return True, "Campo limpo"
        
    except Exception as e:
        logging.error(f"Erro ao limpar campo {seletor}: {e}")
        return False, f"Erro na limpeza: {e}"


def verificar_campo_preenchido(pagina, seletor: str) -> bool:
    """
    Verifica se um campo está preenchido na página.
    
    Args:
        pagina: Página do Playwright
        seletor (str): Seletor do campo
    
    Returns:
        bool: True se campo está preenchido
    
    Fluxo: Usado para verificar estado atual dos campos
    """
    try:
        if not _elemento_existe(pagina, seletor):
            return False
        
        elemento = pagina.locator(seletor)
        valor = elemento.input_value()
        
        return bool(valor and valor.strip())
        
    except Exception as e:
        logging.warning(f"Erro ao verificar campo preenchido {seletor}: {e}")
        return False


def fechar_aviso_de_cookies(pagina) -> bool:
    """
    Tenta fechar avisos de cookies automaticamente.
    
    Args:
        pagina: Página do Playwright
    
    Returns:
        bool: True se conseguiu fechar aviso
    
    Fluxo: Chamado automaticamente antes de executar outras ações
    """
    seletores_cookies = [
        "[id*='cookie'] button",
        "[class*='cookie'] button", 
        "button[class*='accept']",
        "button[class*='aceitar']",
        "button:has-text('Aceitar')",
        "button:has-text('Accept')",
        "button:has-text('OK')",
        ".cookie-banner button",
        ".cookie-notice button",
        "#cookie-banner button",
        "#cookie-notice button"
    ]
    
    try:
        for seletor in seletores_cookies:
            try:
                if pagina.locator(seletor).count() > 0:
                    pagina.locator(seletor).first.click(timeout=2000)
                    logging.info(f"Aviso de cookies fechado usando: {seletor}")
                    time.sleep(1)  # Aguardar animação
                    return True
            except:
                continue
        
        logging.info("Nenhum aviso de cookies encontrado para fechar")
        return False
        
    except Exception as e:
        logging.warning(f"Erro ao fechar avisos de cookies: {e}")
        return False


def verificar_estado_campos_formulario(page, seletores_campos: list) -> Dict[str, Any]:
    """
    Verifica estado atual de múltiplos campos de formulário.
    
    Args:
        page: Página do Playwright
        seletores_campos (list): Lista de seletores para verificar
    
    Returns:
        Dict: Estado dos campos {seletor: {preenchido: bool, valor: str}}
    
    Fluxo: Usado para análise completa do estado do formulário
    """
    estado = {}
    
    try:
        for seletor in seletores_campos:
            try:
                if _elemento_existe(page, seletor):
                    elemento = page.locator(seletor)
                    valor = elemento.input_value()
                    
                    estado[seletor] = {
                        "preenchido": bool(valor and valor.strip()),
                        "valor": valor or "",
                        "visivel": True
                    }
                else:
                    estado[seletor] = {
                        "preenchido": False,
                        "valor": "",
                        "visivel": False
                    }
                    
            except Exception as e:
                logging.warning(f"Erro ao verificar campo {seletor}: {e}")
                estado[seletor] = {
                    "preenchido": False,
                    "valor": "",
                    "visivel": False,
                    "erro": str(e)
                }
        
        logging.info(f"Estado verificado para {len(seletores_campos)} campos")
        return estado
        
    except Exception as e:
        logging.error(f"Erro ao verificar estado dos campos: {e}")
        return {}


def executar_acao_com_retry(pagina, resposta_llm: str, max_tentativas: int = 3) -> Tuple[bool, str]:
    """
    Executa ação com retry automático em caso de falha.
    
    Args:
        pagina: Página do Playwright
        resposta_llm (str): Resposta JSON do LLM
        max_tentativas (int): Número máximo de tentativas
    
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    
    Fluxo: Wrapper para executar_acao com retry automático
    """
    for tentativa in range(max_tentativas):
        try:
            sucesso, mensagem = executar_acao(pagina, resposta_llm)
            
            if sucesso:
                return True, mensagem
            
            if tentativa < max_tentativas - 1:
                logging.info(f"Tentativa {tentativa + 1} falhou, tentando novamente...")
                time.sleep(1)  # Aguardar antes de retry
            
        except Exception as e:
            if tentativa < max_tentativas - 1:
                logging.warning(f"Erro na tentativa {tentativa + 1}: {e}")
                time.sleep(1)
            else:
                return False, f"Falha após {max_tentativas} tentativas: {e}"
    
    return False, f"Falha após {max_tentativas} tentativas"
