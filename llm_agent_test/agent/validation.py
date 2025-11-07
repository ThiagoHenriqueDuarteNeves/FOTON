"""
Módulo de Validação - Validações de objetivos e respostas LLM
Centraliza toda lógica de validação para facilitar manutenção e testes.

Fluxo de Execução:
- Chamado após cada ação para verificar se objetivo foi atingido
- Usado para validar respostas do LLM antes de executar ações
- Fornece heurísticas para determinar sucesso/falha de operações
"""
import logging
import json
from typing import Optional, Tuple, Dict, Any


def objetivo_atingido(pagina, instrucoes: str, url_antes: Optional[str] = None, 
                     url_depois: Optional[str] = None) -> Tuple[bool, str]:
    """
    Determina se o objetivo declarado foi cumprido usando heurísticas.
    
    Args:
        pagina: Objeto da página do Playwright
        instrucoes (str): Instruções/objetivo fornecido pelo usuário
        url_antes (str, optional): URL antes da ação
        url_depois (str, optional): URL depois da ação
    
    Returns:
        Tuple[bool, str]: (objetivo_atingido, motivo)
    
    Fluxo: Chamado após cada ação para verificar se deve continuar ou parar
    """
    try:
        instr = (instrucoes or "").lower()
        
        # Só encerramos automaticamente se a instrução pedir explicitamente para finalizar
        pedido_finalizar = any(t in instr for t in ["finalizar", "encerrar", "concluir", "terminar"])
        
        if any(t in instr for t in ["cpf", "senha", "login", "entrar", "acessar"]) and pedido_finalizar:
            # 1) Se houve navegação e não estamos mais numa URL de login
            if url_antes and url_depois and url_depois != url_antes and 'login' not in (url_depois or '').lower():
                return True, "Mudança de URL pós-login detectada"
            
            # 2) Se não há mais campo de senha na página e há indicadores de sessão ativa
            try:
                if pagina.locator("input[type='password']").count() == 0:
                    # Verificar indicadores de sessão ativa
                    indicadores_sessao = [
                        "Sair", "Logout", "Minha Conta", "Perfil", "Bem-vindo", "Olá",
                        "Dashboard", "Área do Candidato", "Minha Área"
                    ]
                    
                    texto_pagina = pagina.text_content("body") or ""
                    
                    for indicador in indicadores_sessao:
                        if indicador.lower() in texto_pagina.lower():
                            return True, f"Indicador de sessão ativa encontrado: {indicador}"
                            
            except Exception as e:
                logging.warning(f"Erro ao verificar campos na página: {e}")
                
        # Por padrão, não considerar objetivo atingido
        return False, "Objetivo não atingido automaticamente"
        
    except Exception as e:
        logging.error(f"Erro na validação de objetivo: {e}")
        return False, f"Erro na validação: {e}"


def validar_resposta_llm(resposta: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Valida se resposta do LLM está em formato JSON válido.
    
    Args:
        resposta (str): Resposta bruta do LLM
    
    Returns:
        Tuple[bool, Dict|None, str]: (é_válida, dados_json, motivo)
    
    Fluxo: Chamado após receber resposta do LLM para validar antes de executar
    """
    try:
        if not resposta or not resposta.strip():
            return False, None, "Resposta vazia"
            
        # Importar extrair_json_da_resposta para processar resposta completa
        from agent.json_parser import extrair_json_da_resposta
        
        # Usar o parser robusto que remove <think>, markdown, etc
        dados_json = extrair_json_da_resposta(resposta)
        
        if not dados_json:
            return False, None, "Falha ao extrair JSON da resposta"
            
        # Validar estrutura básica
        if not isinstance(dados_json, dict):
            return False, None, "JSON não é um objeto"
            
        # Validar campos obrigatórios
        if "action" not in dados_json:
            return False, None, "Campo 'action' obrigatório não encontrado"
            
        if "selector" not in dados_json:
            return False, None, "Campo 'selector' obrigatório não encontrado"
            
        return True, dados_json, "JSON válido"
            
    except Exception as e:
        return False, None, f"Erro na validação: {e}"


def validar_seletor_existente(seletor: str, seletores_validos: list) -> Tuple[bool, str]:
    """
    Valida se seletor existe na lista de seletores válidos extraídos da página.
    
    Args:
        seletor (str): Seletor a validar
        seletores_validos (list): Lista de seletores extraídos da página
    
    Returns:
        Tuple[bool, str]: (é_válido, motivo)
    
    Fluxo: Chamado após validar JSON para verificar se seletor existe na página
    """
    try:
        if not seletor:
            return False, "Seletor vazio"
            
        if not seletores_validos:
            return False, "Lista de seletores válidos vazia"
            
        # Normalizar seletor para comparação
        seletor_normalizado = seletor.strip()
        
        # 1. Verificar se seletor existe exatamente na lista
        if seletor_normalizado in seletores_validos:
            return True, "Seletor encontrado na lista"
            
        # 2. Verificar variações comuns (case insensitive)
        for seletor_valido in seletores_validos:
            if seletor_normalizado.lower() == seletor_valido.lower():
                return True, f"Seletor encontrado (case insensitive): {seletor_valido}"
        
        # 3. Validação especial para campos de cadastro customer.*
        # Estes campos SÓ devem ser aceitos se realmente existirem na página
        if '#customer.' in seletor_normalizado or 'customer.' in seletor_normalizado:
            # Para campos de cadastro, exigir que estejam na lista de seletores válidos
            # Verificar se há algum campo customer.* na página
            tem_campos_customer = any('#customer.' in sel or 'customer.' in sel for sel in seletores_validos)
            if not tem_campos_customer:
                return False, f"Campos customer.* não encontrados na página atual. Navegue para a página de cadastro primeiro."
        
        # 4. Validação restrita - só aceitar seletores que realmente existem na página
        # REMOVIDO: validação permissiva que aceitava qualquer seletor CSS válido
        # Agora prioriza verificação de existência real na página
        
        # 5. Verificação de similaridade de seletores existentes na página
        for seletor_valido in seletores_validos:
            # Extrair partes do seletor (nome, id, classe)
            if '[name=' in seletor_normalizado and '[name=' in seletor_valido:
                # Comparar o valor do atributo name
                try:
                    nome_solicitado = seletor_normalizado.split("name='")[1].split("'")[0]
                    nome_valido = seletor_valido.split("name='")[1].split("'")[0] if "name='" in seletor_valido else ""
                    if nome_solicitado == nome_valido:
                        return True, f"Seletor por name={nome_solicitado} compatível"
                except:
                    pass
            
            # Verificar compatibilidade de classes
            if seletor_normalizado.startswith('.') and ('.' in seletor_valido or 'class' in seletor_valido):
                return True, f"Seletor de classe compatível"
                
        return False, f"Seletor não encontrado na lista de {len(seletores_validos)} seletores válidos"
        
    except Exception as e:
        return False, f"Erro na validação de seletor: {e}"


def validar_acao_permitida(acao: str) -> Tuple[bool, str]:
    """
    Valida se ação é permitida pelo sistema.
    
    Args:
        acao (str): Ação solicitada (click, fill, etc.)
    
    Returns:
        Tuple[bool, str]: (é_permitida, motivo)
    
    Fluxo: Chamado após validar JSON para verificar se ação é suportada
    """
    acoes_permitidas = [
        "click", "fill", "select", "wait", "scroll", 
        "hover", "press", "type", "clear", "submit"
    ]
    
    try:
        if not acao:
            return False, "Ação vazia"
            
        acao_normalizada = acao.strip().lower()
        
        if acao_normalizada in acoes_permitidas:
            return True, "Ação permitida"
        else:
            return False, f"Ação '{acao}' não permitida. Ações válidas: {', '.join(acoes_permitidas)}"
            
    except Exception as e:
        return False, f"Erro na validação de ação: {e}"


def validar_valor_preenchimento(acao: str, valor: Optional[str]) -> Tuple[bool, str]:
    """
    Valida se valor é adequado para ação de preenchimento.
    
    Args:
        acao (str): Tipo da ação
        valor (str, optional): Valor a ser preenchido
    
    Returns:
        Tuple[bool, str]: (é_válido, motivo)
    
    Fluxo: Chamado para ações de preenchimento para validar valor
    """
    try:
        acoes_que_precisam_valor = ["fill", "type", "select"]
        
        if acao.lower() in acoes_que_precisam_valor:
            if not valor:
                return False, f"Ação '{acao}' requer valor não vazio"
            if len(valor.strip()) == 0:
                return False, f"Valor para ação '{acao}' não pode ser apenas espaços"
                
        return True, "Valor válido para a ação"
        
    except Exception as e:
        return False, f"Erro na validação de valor: {e}"
