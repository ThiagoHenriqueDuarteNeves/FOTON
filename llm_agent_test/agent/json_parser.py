"""
Módulo de Processamento JSON - Limpeza e validação de respostas LLM
Centraliza toda lógica de parsing e sanitização de JSON para facilitar manutenção.

Fluxo de Execução:
- Recebe resposta bruta do LLM
- Remove markdown e formatos indesejados
- Sanitiza e corrige JSON malformado
- Valida estrutura e campos obrigatórios
- Retorna JSON limpo e validado
"""
import logging
import json
import re
from typing import Optional, Dict, Any, Tuple

PT_TO_EN_KEY_MAP = {
    "acao": "action",
    "ação": "action",
    "seletor": "selector",
    "valor": "value",
    "confianca": "confidence",
    "confiança": "confidence",
    "justificativa": "reason",
    "motivo": "reason",
}

REQUIRED_KEYS = {"action", "selector"}


def extrair_json_da_resposta(resposta_llm: str) -> Optional[Dict[str, Any]]:
    """
    Extrai JSON válido de resposta do LLM.
    
    Args:
        resposta_llm (str): Resposta bruta do LLM
    
    Returns:
        Dict: JSON extraído ou None se falhou
    
    Fluxo: Primeira função chamada para processar resposta do LLM
    """
    try:
        if not resposta_llm or not resposta_llm.strip():
            logging.warning("Resposta LLM vazia")
            return None
        
        # Tentar sanitizar e parsear
        json_sanitizado = sanitizar_e_parsear_json(resposta_llm)
        
        if json_sanitizado:
            logging.info("JSON extraído com sucesso")
            return json_sanitizado
        else:
            logging.warning("Falha ao extrair JSON da resposta")
            return None
            
    except Exception as e:
        logging.error(f"Erro ao extrair JSON: {e}")
        return None


def sanitizar_e_parsear_json(resposta_bruta: str) -> Optional[Dict[str, Any]]:
    """
    Sanitiza e parseia JSON de resposta potencialmente malformada.
    
    Args:
        resposta_bruta (str): Resposta bruta do LLM
    
    Returns:
        Dict: JSON parseado ou None se falhou
    
    Fluxo: Função principal para limpeza de JSON malformado
    """
    try:
        if not resposta_bruta or not resposta_bruta.strip():
            return None
        
        texto_sem_markdown = _remover_markdown(resposta_bruta)
        texto_processado = _remover_blocos_think(texto_sem_markdown)

        json_extraido = _extrair_bloco_json(texto_processado)
        
        if not json_extraido:
            return None
        
        # Limpar e normalizar JSON
        json_normalizado = _normalizar_json_string(json_extraido)
        
        resultado = _parsear_json_seguro(json_normalizado)
        
        if isinstance(resultado, dict):
            resultado = _normalizar_chaves_portugues(resultado)

            if _validar_estrutura_json(resultado):
                return resultado
        
        return None
        
    except Exception as e:
        logging.error(f"Erro ao sanitizar JSON: {e}")
        return None


def extract_last_json_object(content: str) -> Optional[Dict[str, Any]]:
    """Retorna o último objeto JSON válido encontrado, já normalizado."""
    return sanitizar_e_parsear_json(content)


extractLastJsonObject = extract_last_json_object


def _remover_markdown(texto: str) -> str:
    """Remove blocos markdown preservando o conteúdo interno."""
    if not texto:
        return ""

    def _replace(match: re.Match) -> str:
        inner = match.group(1)
        return inner.strip() if inner else ""

    texto_sem_cercas = re.sub(r'```(?:json)?\s*([\s\S]*?)```', _replace, texto, flags=re.IGNORECASE)
    return texto_sem_cercas.strip()


def _remover_blocos_think(texto: str) -> str:
    """Remove blocos <think>...</think> da resposta do LLM."""
    if not texto:
        return ""
    return re.sub(r'<think>[\s\S]*?</think>', ' ', texto, flags=re.IGNORECASE).strip()


def _extrair_ultimo_json_balanceado(texto: str) -> Optional[str]:
    """Retorna o último bloco JSON bem-balanceado encontrado no texto."""
    if not texto:
        return None

    stack = []
    in_string = False
    escape = False
    ultimo_inicio = None
    ultimo_fim = None

    for indice, caractere in enumerate(texto):
        if in_string:
            if escape:
                escape = False
                continue
            if caractere == '\\':
                escape = True
                continue
            if caractere == '"':
                in_string = False
            continue

        if caractere == '"':
            in_string = True
            continue

        if caractere == '{':
            stack.append(indice)
            continue

        if caractere == '}' and stack:
            inicio = stack.pop()
            if not stack:
                ultimo_inicio = inicio
                ultimo_fim = indice + 1

    if ultimo_inicio is not None and ultimo_fim is not None:
        return texto[ultimo_inicio:ultimo_fim].strip()

    return None


def _extrair_bloco_json(texto: str) -> Optional[str]:
    """Extrai o último bloco JSON plausível presente no texto."""
    if not texto:
        return None

    ultimo_balanceado = _extrair_ultimo_json_balanceado(texto)
    if ultimo_balanceado:
        return ultimo_balanceado

    padroes = [
        r'\{.*?\}',
        r'\{.*?\}\s*$',
        r'^\s*\{.*?\}',
    ]

    candidato = None
    for padrao in padroes:
        matches = re.findall(padrao, texto, re.DOTALL)
        for match in matches:
            if _parece_json(match):
                candidato = match.strip()

    if candidato:
        return candidato

    if _parece_json(texto):
        return texto.strip()

    return None


def _parece_json(texto: str) -> bool:
    """
    Verifica se texto parece ser JSON.
    
    Args:
        texto (str): Texto para verificar
    
    Returns:
        bool: True se parece JSON
    """
    texto = texto.strip()
    
    # Deve começar com { e terminar com }
    if not (texto.startswith('{') and texto.endswith('}')):
        return False
    
    # Deve conter pelo menos uma chave comum
    chaves_comuns = ['action', 'selector', 'value', 'reasoning', 'type', 'acao', 'seletor', 'valor', 'justificativa', 'confianca', 'motivo']
    return any(f'"{chave}"' in texto for chave in chaves_comuns)


def _normalizar_json_string(json_str: str) -> str:
    """
    Normaliza string JSON corrigindo problemas comuns.
    
    Args:
        json_str (str): String JSON para normalizar
    
    Returns:
        str: JSON normalizado
    """
    # Remover quebras de linha desnecessárias dentro de strings
    json_str = re.sub(r'"\s*\n\s*"', '""', json_str)
    
    # Corrigir aspas simples para duplas (quando apropriado)
    json_str = re.sub(r"'([^']*)'(\s*:\s*)", r'"\1"\2', json_str)
    json_str = re.sub(r'(\s*:\s*)"([^"]*)"', r'\1"\2"', json_str)
    
    # Remover comentários JavaScript
    json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
    
    # Remover vírgulas extras antes de }
    json_str = re.sub(r',(\s*})', r'\1', json_str)
    
    # Garantir que valores booleanos estejam em minúscula
    json_str = re.sub(r':\s*True\b', ': true', json_str)
    json_str = re.sub(r':\s*False\b', ': false', json_str)
    
    # Garantir que null esteja em minúscula
    json_str = re.sub(r':\s*None\b', ': null', json_str)
    
    return json_str.strip()


def _normalizar_chaves_portugues(json_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza chaves do português para o inglês padrão."""
    if not isinstance(json_obj, dict):
        return json_obj

    normalizado: Dict[str, Any] = {}
    for chave, valor in json_obj.items():
        chave_str = chave if isinstance(chave, str) else str(chave)
        chave_normalizada = PT_TO_EN_KEY_MAP.get(chave_str.lower(), chave_str)
        if isinstance(valor, dict):
            valor = _normalizar_chaves_portugues(valor)
        normalizado[chave_normalizada] = valor

    return normalizado


def _parsear_json_seguro(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Tenta parsear JSON com múltiplas estratégias.
    
    Args:
        json_str (str): String JSON para parsear
    
    Returns:
        Dict: JSON parseado ou None
    """
    # Estratégia 1: Parse direto
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Estratégia 2: Parse com eval (mais perigoso, mas às vezes funciona)
    try:
        # Substituir valores JavaScript por Python
        js_to_py = json_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        resultado = eval(js_to_py)
        if isinstance(resultado, dict):
            return resultado
    except:
        pass
    
    # Estratégia 3: Parse manual por regex
    try:
        return _parsear_json_manual(json_str)
    except:
        pass
    
    return None


def _parsear_json_manual(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse manual de JSON simples usando regex.
    
    Args:
        json_str (str): String JSON
    
    Returns:
        Dict: JSON parseado ou None
    """
    resultado = {}
    
    # Extrair pares chave-valor
    padrao = r'"([^"]+)"\s*:\s*"([^"]*)"'  # String values
    matches = re.findall(padrao, json_str)
    
    for chave, valor in matches:
        resultado[chave] = valor
    
    # Extrair valores não-string
    padrao_outros = r'"([^"]+)"\s*:\s*([^,}]+)'
    matches_outros = re.findall(padrao_outros, json_str)
    
    for chave, valor in matches_outros:
        valor = valor.strip()
        if chave not in resultado:  # Não sobrescrever strings
            if valor.lower() == 'true':
                resultado[chave] = True
            elif valor.lower() == 'false':
                resultado[chave] = False
            elif valor.lower() == 'null':
                resultado[chave] = None
            elif valor.isdigit():
                resultado[chave] = int(valor)
            else:
                resultado[chave] = valor
    
    return resultado if resultado else None


def _validar_estrutura_json(json_obj: Dict[str, Any]) -> bool:
    """
    Valida se JSON tem estrutura esperada.
    
    Args:
        json_obj (Dict): JSON para validar
    
    Returns:
        bool: True se estrutura é válida
    """
    # Deve ser um dicionário
    if not isinstance(json_obj, dict):
        return False
    
    faltantes = [chave for chave in REQUIRED_KEYS if chave not in json_obj]
    if faltantes:
        logging.warning(
            "JSON não possui chaves obrigatórias %s | chaves encontradas: %s",
            faltantes,
            list(json_obj.keys()),
        )
        return False

    return True


def normalizar_seletor(seletor: str) -> str:
    """
    Normaliza seletor CSS removendo espaços e caracteres problemáticos.
    
    Args:
        seletor (str): Seletor CSS para normalizar
    
    Returns:
        str: Seletor normalizado
    
    Fluxo: Chamado antes de validar seletor na página
    """
    try:
        if not seletor:
            return ""
        
        # Remover espaços extras
        seletor_limpo = seletor.strip()
        
        # Remover quebras de linha
        seletor_limpo = re.sub(r'\n+', ' ', seletor_limpo)
        
        # Normalizar espaços múltiplos
        seletor_limpo = re.sub(r'\s+', ' ', seletor_limpo)
        
        # Remover espaços ao redor de operadores CSS
        seletor_limpo = re.sub(r'\s*([>+~])\s*', r'\1', seletor_limpo)
        
        return seletor_limpo
        
    except Exception as e:
        logging.warning(f"Erro ao normalizar seletor '{seletor}': {e}")
        return seletor


def seletor_esta_na_lista(seletor: str, lista_permitida: list) -> bool:
    """
    Verifica se seletor está na lista de seletores permitidos.
    
    Args:
        seletor (str): Seletor para verificar
        lista_permitida (list): Lista de seletores válidos
    
    Returns:
        bool: True se seletor é válido
    
    Fluxo: Usado para validar seletores antes de executar ação
    """
    try:
        if not seletor or not lista_permitida:
            return False
        
        seletor_normalizado = normalizar_seletor(seletor)
        
        # Verificação exata
        if seletor_normalizado in lista_permitida:
            return True
        
        # Verificação case-insensitive
        seletor_lower = seletor_normalizado.lower()
        for seletor_valido in lista_permitida:
            if seletor_lower == seletor_valido.lower():
                return True
        
        # Verificação de similaridade (para pequenas diferenças)
        for seletor_valido in lista_permitida:
            if _seletores_similares(seletor_normalizado, seletor_valido):
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"Erro ao verificar seletor na lista: {e}")
        return False


def _seletores_similares(seletor1: str, seletor2: str) -> bool:
    """
    Verifica se dois seletores são similares.
    
    Args:
        seletor1, seletor2 (str): Seletores para comparar
    
    Returns:
        bool: True se são similares
    """
    # Remover diferenças menores como espaços extras
    s1 = re.sub(r'\s+', '', seletor1.lower())
    s2 = re.sub(r'\s+', '', seletor2.lower())
    
    # Se são idênticos após limpeza
    if s1 == s2:
        return True
    
    # Se um contém o outro (para seletores hierárquicos)
    if len(s1) > 5 and len(s2) > 5:  # Evitar falsos positivos com seletores muito curtos
        if s1 in s2 or s2 in s1:
            return True
    
    return False


def extrair_e_validar_json(resposta_llm: str, seletores_validos: list = None) -> Tuple[bool, Optional[Dict], str]:
    """
    Pipeline completo: extrai, valida e verifica JSON da resposta LLM.
    
    Args:
        resposta_llm (str): Resposta do LLM
        seletores_validos (list, optional): Lista de seletores válidos
    
    Returns:
        Tuple[bool, Dict|None, str]: (sucesso, json_extraido, motivo)
    
    Fluxo: Função de conveniência que combina extração e validação
    """
    try:
        # Etapa 1: Extrair JSON
        json_extraido = extrair_json_da_resposta(resposta_llm)
        
        if not json_extraido:
            return False, None, "Não foi possível extrair JSON válido"
        
        # Etapa 2: Validar campos obrigatórios
        if 'action' not in json_extraido:
            return False, json_extraido, "Campo 'action' obrigatório não encontrado"
        
        if 'selector' not in json_extraido:
            return False, json_extraido, "Campo 'selector' obrigatório não encontrado"
        
        # Etapa 3: Validar seletor se lista fornecida
        if seletores_validos:
            seletor = json_extraido.get('selector', '')
            if not seletor_esta_na_lista(seletor, seletores_validos):
                return False, json_extraido, f"Seletor '{seletor}' não está na lista de seletores válidos"
        
        return True, json_extraido, "JSON válido e verificado"
        
    except Exception as e:
        logging.error(f"Erro no pipeline de validação JSON: {e}")
        return False, None, f"Erro na validação: {e}"


def corrigir_json_comum(json_str: str) -> str:
    """
    Aplica correções comuns em JSON malformado.
    
    Args:
        json_str (str): JSON possivelmente malformado
    
    Returns:
        str: JSON com correções aplicadas
    
    Fluxo: Usado como etapa de pré-processamento antes do parse
    """
    try:
        # Correção 1: Adicionar aspas em chaves sem aspas
        json_str = re.sub(r'(\w+)(\s*:\s*)', r'"\1"\2', json_str)
        
        # Correção 2: Corrigir aspas simples em valores string
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        
        # Correção 3: Remover vírgula no final antes de }
        json_str = re.sub(r',(\s*})', r'\1', json_str)
        
        # Correção 4: Adicionar vírgulas faltando
        json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
        
        # Correção 5: Escapar aspas dentro de strings
        json_str = re.sub(r':\s*"([^"]*)"([^"]*)"([^"]*)"', r': "\1\\\"\2\\\"\3"', json_str)
        
        return json_str
        
    except Exception as e:
        logging.warning(f"Erro ao corrigir JSON: {e}")
        return json_str


def debug_json_parsing(resposta_llm: str) -> Dict[str, Any]:
    """
    Função de debug para analisar problemas de parsing JSON.
    
    Args:
        resposta_llm (str): Resposta problemática
    
    Returns:
        Dict: Informações de debug
    
    Fluxo: Usado para diagnosticar problemas de parsing
    """
    debug_info = {
        "resposta_original": resposta_llm[:500],  # Primeiros 500 chars
        "tamanho_resposta": len(resposta_llm),
        "tem_markdown": "```" in resposta_llm,
        "tem_chaves": "{" in resposta_llm and "}" in resposta_llm,
        "tentativas": []
    }
    
    # Tentativa 1: Parse direto
    try:
        json.loads(resposta_llm)
        debug_info["tentativas"].append({"metodo": "parse_direto", "sucesso": True})
    except Exception as e:
        debug_info["tentativas"].append({"metodo": "parse_direto", "sucesso": False, "erro": str(e)})
    
    # Tentativa 2: Remover markdown
    texto_limpo = _remover_markdown(resposta_llm)
    try:
        json.loads(texto_limpo)
        debug_info["tentativas"].append({"metodo": "sem_markdown", "sucesso": True})
    except Exception as e:
        debug_info["tentativas"].append({"metodo": "sem_markdown", "sucesso": False, "erro": str(e)})
    
    # Tentativa 3: Pipeline completo
    try:
        resultado = sanitizar_e_parsear_json(resposta_llm)
        debug_info["tentativas"].append({
            "metodo": "pipeline_completo", 
            "sucesso": resultado is not None,
            "resultado": resultado
        })
    except Exception as e:
        debug_info["tentativas"].append({"metodo": "pipeline_completo", "sucesso": False, "erro": str(e)})
    
    return debug_info
