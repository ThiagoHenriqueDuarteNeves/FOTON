"""
Módulo de Análise de HTML - Extração e processamento de elementos HTML
Centraliza toda lógica de parsing e extração de seletores para facilitar manutenção.

Fluxo de Execução:
- Recebe página do navegador
- Extrai HTML e converte para BeautifulSoup
- Gera seletores CSS otimizados
- Identifica elementos interativos
- Prioriza elementos por contexto
"""
import logging
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple


def extrair_html(pagina) -> str:
    """
    Extrai o HTML da página atual.
    
    Args:
        pagina: Objeto da página do Playwright
    
    Returns:
        str: HTML da página
    
    Fluxo: Primeiro passo na análise de qualquer página
    """
    try:
        return pagina.content()
    except Exception as e:
        logging.error(f"Erro ao extrair HTML: {e}")
        return ""


def escapar_css_id(id_value: str) -> str:
    """
    Escapa caracteres especiais em IDs CSS.
    
    Args:
        id_value (str): Valor do ID para escapar
    
    Returns:
        str: ID escapado para uso em seletores CSS
    
    Fluxo: Chamado durante geração de seletores para IDs problemáticos
    """
    if not id_value:
        return ""
    
    # Escapar caracteres especiais comuns em IDs
    caracteres_especiais = {
        ':': '\\:',
        '.': '\\.',
        '[': '\\[',
        ']': '\\]',
        '(': '\\(',
        ')': '\\)',
        ' ': '\\ ',
        '#': '\\#',
        '!': '\\!',
        '"': '\\"',
        "'": "\\'",
        '@': '\\@',
        '$': '\\$',
        '%': '\\%',
        '^': '\\^',
        '&': '\\&',
        '*': '\\*',
        '+': '\\+',
        '=': '\\=',
        '~': '\\~',
        '`': '\\`',
        '|': '\\|',
        '\\': '\\\\'
    }
    
    resultado = id_value
    for char, escape in caracteres_especiais.items():
        resultado = resultado.replace(char, escape)
    
    return resultado


def gerar_selector(el) -> str:
    """
    Gera seletor CSS único para elemento HTML.
    
    Args:
        el: Elemento BeautifulSoup
    
    Returns:
        str: Seletor CSS otimizado
    
    Fluxo: Chamado para cada elemento interativo identificado
    """
    try:
        # Prioridade 1: name para inputs de formulário (mais confiável que IDs com pontos)
        if el.name in ['input', 'select', 'textarea'] and el.get('name'):
            return f"[name='{el['name']}']"
        
        # Prioridade 2: ID único
        if el.get('id'):
            id_original = el['id']
            id_escapado = escapar_css_id(id_original)
            seletor_id = f"#{id_escapado}"
            
            # Debug para IDs com pontos
            if '.' in id_original:
                print(f"🔍 [DEBUG] ID com ponto detectado: '{id_original}' → '#{id_escapado}'")
                
            return seletor_id
        
        # Prioridade 3: data-testid (mais estável)
        if el.get('data-testid'):
            return f"[data-testid='{el['data-testid']}']"
        
        # Prioridade 4: Seletores específicos para elementos comuns
        if el.name == 'input':
            if el.get('type') == 'submit' and el.get('value'):
                return f"input[type='submit'][value='{el['value']}']"
            elif el.get('type') == 'button' and el.get('value'):
                return f"input[type='button'][value='{el['value']}']"
            elif el.get('class'):
                classes = el['class'] if isinstance(el['class'], list) else [el['class']]
                return f"input[class='{' '.join(classes)}']"
        
        # Prioridade 4.5: Botões com texto curto e único - usar button:has-text()
        if el.name == 'button':
            texto = el.get_text(strip=True) if hasattr(el, 'get_text') else ''
            # Se texto curto (até 20 chars) e não vazio, pode ser identificador único
            if texto and len(texto) <= 20 and len(texto.strip()) > 0:
                # Usar sintaxe Playwright button:has-text("texto")
                texto_limpo = texto.strip()
                return f"button:has-text('{texto_limpo}')"
        
        # Prioridade 5: class específica única ou combinação de classes
        if el.get('class'):
            classes = el['class'] if isinstance(el['class'], list) else [el['class']]
            # Filtrar classes significativas (não utilitárias do Bootstrap/Tailwind)
            classes_relevantes = []
            classes_utilitarias = {'p-1', 'p-2', 'p-3', 'p-4', 'p-5', 'm-1', 'm-2', 'm-3', 'm-4', 'm-5', 
                                  'fw-bold', 'fw-normal', 'text-uppercase', 'text-lowercase', 
                                  'd-flex', 'd-block', 'd-none', 'w-100', 'h-100'}
            
            for cls in classes:
                # Pular classes muito curtas ou utilitárias
                if cls and len(cls) > 1 and cls not in classes_utilitarias:
                    classes_relevantes.append(cls)
            
            # Se temos múltiplas classes relevantes, combinar para seletor mais específico
            if len(classes_relevantes) >= 2:
                # Combinar até 2 classes mais relevantes (btn + btn-primary)
                return f".{'.'.join(classes_relevantes[:2])}"
            elif len(classes_relevantes) == 1:
                return f".{classes_relevantes[0]}"
        
        # Prioridade 6: combinação tag + atributos
        seletor_base = el.name
        
        # Adicionar tipo para inputs
        if el.name == 'input' and el.get('type'):
            seletor_base += f"[type='{el['type']}']"
        
        # Adicionar placeholder
        if el.get('placeholder'):
            placeholder_limpo = el['placeholder'][:30]  # Limitar tamanho
            seletor_base += f"[placeholder*='{placeholder_limpo}']"
        
        # Adicionar value se específico
        if el.get('value') and len(el['value']) < 30:  # Aumentando limite
            seletor_base += f"[value='{el['value']}']"
        
        # Para links (a), usar texto como identificador específico
        if el.name == 'a' and el.get_text(strip=True):
            texto = el.get_text(strip=True)
            if len(texto) < 30:  # Texto não muito longo
                # Usar seletor compatível com Playwright
                texto_escapado = texto.replace("'", "\\'")
                return f"a >> text='{texto_escapado}'"
        
        # Para elementos com href, incluir no seletor
        if el.get('href') and len(el['href']) < 50:
            seletor_base += f"[href='{el['href']}']"
        
        return seletor_base
        
    except Exception as e:
        logging.warning(f"Erro ao gerar seletor para elemento {el.name}: {e}")
        return el.name if el and hasattr(el, 'name') else "unknown"


def _identificar_formulario_principal(soup: BeautifulSoup) -> Optional[Any]:
    """
    Identifica o formulário principal da página (maior e mais relevante).
    
    Args:
        soup: BeautifulSoup object da página
    
    Returns:
        Elemento do formulário principal ou None
    """
    formularios = soup.find_all('form')
    
    if not formularios:
        return None
    
    if len(formularios) == 1:
        return formularios[0]
    
    # Se há múltiplos formulários, escolher o maior (mais campos)
    melhor_form = None
    max_campos = 0
    
    for form in formularios:
        # Contar inputs, textareas e selects dentro do formulário
        campos = form.find_all(['input', 'textarea', 'select'])
        num_campos = len([c for c in campos if c.get('type') not in ['submit', 'button', 'hidden']])
        
        if num_campos > max_campos:
            max_campos = num_campos
            melhor_form = form
    
    return melhor_form


def _pertence_ao_formulario(elemento, formulario) -> bool:
    """
    Verifica se um elemento pertence a um formulário específico.
    
    Args:
        elemento: Elemento BeautifulSoup
        formulario: Elemento form BeautifulSoup
    
    Returns:
        bool: True se elemento está dentro do formulário
    """
    if not formulario:
        return True  # Se não há formulário definido, aceitar todos
    
    # Verificar se elemento é descendente do formulário
    parent = elemento.parent
    while parent:
        if parent == formulario:
            return True
        parent = parent.parent
    
    return False


def extrair_elementos_interativos_completos(soup: BeautifulSoup, page) -> List[Dict[str, Any]]:
    """
    Extrai todos os elementos interativos de uma página com informações completas.
    
    Args:
        soup: BeautifulSoup object da página
        page: Página Playwright para verificações de visibilidade
    
    Returns:
        List[Dict]: Lista de elementos com informações detalhadas
    
    Fluxo: Função principal para identificar todos elementos interativos
    """
    elementos = []
    
    try:
        # Identificar o formulário principal (maior e mais relevante)
        formulario_principal = _identificar_formulario_principal(soup)
        
        # Inputs (campos de texto, checkbox, radio, etc.)
        for campo in soup.find_all(['input', 'textarea', 'select']):
            if _elemento_visivel_e_habilitado(campo, page):
                # Filtrar campos que pertencem ao formulário principal
                if formulario_principal and not _pertence_ao_formulario(campo, formulario_principal):
                    continue
                    
                info_campo = _extrair_info_campo(campo, soup)
                if info_campo:
                    elementos.append(info_campo)
        
        # Botões - busca separada para cada tipo
        # Botões HTML normais
        for botao in soup.find_all('button'):
            if _elemento_visivel_e_habilitado(botao, page):
                info_botao = _extrair_info_botao(botao)
                if info_botao:
                    elementos.append(info_botao)
        
        # Inputs tipo button e submit
        for botao in soup.find_all('input', type=['submit', 'button']):
            if _elemento_visivel_e_habilitado(botao, page):
                info_botao = _extrair_info_botao(botao)
                if info_botao:
                    elementos.append(info_botao)
        
        # Links importantes
        for link in soup.find_all('a', href=True):
            if _elemento_visivel_e_habilitado(link, page):
                info_link = _extrair_info_link(link)
                if info_link:
                    elementos.append(info_link)
        
        # Elementos com role="button"
        for elemento in soup.find_all(attrs={"role": "button"}):
            if _elemento_visivel_e_habilitado(elemento, page):
                info_role = _extrair_info_role_button(elemento)
                if info_role:
                    elementos.append(info_role)
        
        logging.info(f"Extraídos {len(elementos)} elementos interativos")
        return elementos
        
    except Exception as e:
        logging.error(f"Erro ao extrair elementos interativos: {e}")
        return []


def _elemento_visivel_e_habilitado(elemento, page) -> bool:
    """
    Verifica se elemento está visível e habilitado na página.
    
    Args:
        elemento: Elemento BeautifulSoup
        page: Página Playwright
    
    Returns:
        bool: True se elemento é interativo
    """
    try:
        # Verificações básicas de atributos
        if elemento.get('style') and 'display:none' in elemento['style'].replace(' ', ''):
            return False
        
        if elemento.get('hidden') or elemento.get('disabled'):
            return False
        
        # Verificar se tem seletor válido
        seletor = gerar_selector(elemento)
        if not seletor or seletor == "unknown":
            return False
        
        # Se não temos acesso à página (page=None), assumir visível
        if page is None:
            return True
        
        # Verificação no Playwright (pode falhar, não é crítico)
        try:
            if page.locator(seletor).count() > 0:
                return True
        except Exception as e:
            # Se falhou a verificação no Playwright, mas temos um seletor válido, aceitar
            logging.debug(f"Erro na verificação Playwright para seletor {seletor}: {e}")
            return True  # Mais permissivo
        
        # Se chegou até aqui e tem seletor válido, assumir visível
        return True
        
    except Exception:
        return False


def _extrair_info_campo(campo, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extrai informações detalhadas de um campo de input.
    
    Args:
        campo: Elemento input/textarea/select
        soup: BeautifulSoup object para buscar labels
    
    Returns:
        Dict: Informações do campo ou None se inválido
    """
    try:
        tipo_campo = campo.get('type', 'text') if campo.name == 'input' else campo.name
        seletor = gerar_selector(campo)
        
        # Se não conseguiu gerar seletor válido, pular
        if not seletor or seletor == "unknown":
            return None
        
        # Buscar label associado
        label_texto = _encontrar_label(campo, soup)
        
        # Determinar propósito do campo
        placeholder = campo.get('placeholder', '')
        name = campo.get('name', '')
        id_campo = campo.get('id', '')
        valor_atual = campo.get('value', '').strip()  # Capturar valor atual
        
        # Heurísticas para identificar tipo de dado
        proposito = "texto"
        if any(x in (placeholder + name + id_campo + label_texto).lower() 
               for x in ['email', '@', 'e-mail']):
            proposito = "email"
        elif any(x in (placeholder + name + id_campo + label_texto).lower() 
                 for x in ['senha', 'password', 'pass', 'repeat']):
            proposito = "senha"
        elif any(x in (placeholder + name + id_campo + label_texto).lower() 
                 for x in ['cpf', 'documento']):
            proposito = "cpf"
        elif any(x in (placeholder + name + id_campo + label_texto).lower() 
                 for x in ['telefone', 'phone', 'celular']):
            proposito = "telefone"
        elif tipo_campo in ['checkbox', 'radio']:
            proposito = tipo_campo
        elif campo.name == 'select':
            proposito = "select"
        
        return {
            "tipo": "campo",
            "elemento": campo.name,
            "seletor": seletor,
            "tipo_campo": tipo_campo,
            "proposito": proposito,
            "label": label_texto,
            "placeholder": placeholder,
            "valor_atual": valor_atual,  # Incluir valor atual
            "preenchido": bool(valor_atual),  # Status de preenchimento
            "obrigatorio": bool(campo.get('required')),
            "valor_atual": campo.get('value', ''),
            "name": name,
            "id": id_campo
        }
        
    except Exception as e:
        logging.warning(f"Erro ao extrair info do campo: {e}")
        return None


def _extrair_info_botao(botao) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de um botão.
    
    Args:
        botao: Elemento button ou input[type=button/submit]
    
    Returns:
        Dict: Informações do botão ou None se inválido
    """
    try:
        texto = botao.get_text(strip=True) if hasattr(botao, 'get_text') else botao.get('value', '')
        tipo_botao = botao.get('type', 'button')
        seletor = gerar_selector(botao)
        
        # Se não conseguiu gerar seletor válido, pular
        if not seletor or seletor == "unknown":
            return None
        
        # Validação mínima: deve ter algum texto identificador
        if not texto or len(texto.strip()) < 1:
            return None
        
        # Capturar data-testid se disponível (para ajudar modelo a escolher seletor único)
        testid = botao.get('data-testid', '')
        
        return {
            "tipo": "botao",
            "elemento": botao.name,
            "seletor": seletor,
            "texto": texto,
            "tipo_botao": tipo_botao,
            "acao_provavel": _detectar_acao_botao(texto),
            "data-testid": testid  # Adicionar testid para referência no prompt
        }
        
    except Exception as e:
        logging.warning(f"Erro ao extrair info do botão: {e}")
        return None


def _extrair_info_link(link) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de um link.
    
    Args:
        link: Elemento <a>
    
    Returns:
        Dict: Informações do link ou None se inválido
    """
    try:
        texto = link.get_text(strip=True)
        href = link.get('href', '')
        
        # Validação mínima: deve ter texto ou href válido
        if not texto or len(texto.strip()) < 1:
            return None
        
        seletor = gerar_selector(link)
        testid = link.get('data-testid', '')  # Capturar testid
        
        return {
            "tipo": "link",
            "elemento": "a",
            "seletor": seletor,
            "texto": texto,
            "href": href,
            "acao_provavel": _detectar_acao_link(texto, href),
            "data-testid": testid
        }
        
    except Exception as e:
        logging.warning(f"Erro ao extrair info do link: {e}")
        return None


def _extrair_info_role_button(elemento) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de elemento com role="button".
    
    Args:
        elemento: Elemento com role="button"
    
    Returns:
        Dict: Informações do elemento ou None se inválido
    """
    try:
        texto = elemento.get_text(strip=True)
        
        # Validação mínima: deve ter texto
        if not texto or len(texto.strip()) < 1:
            return None
        
        seletor = gerar_selector(elemento)
        
        return {
            "tipo": "botao_role",
            "elemento": elemento.name,
            "seletor": seletor,
            "texto": texto,
            "role": "button",
            "acao_provavel": _detectar_acao_botao(texto)
        }
        
    except Exception as e:
        logging.warning(f"Erro ao extrair info do elemento role=button: {e}")
        return None


def _encontrar_label(campo, soup: BeautifulSoup) -> str:
    """
    Encontra o label associado a um campo.
    
    Args:
        campo: Elemento do campo
        soup: BeautifulSoup object
    
    Returns:
        str: Texto do label encontrado
    """
    try:
        # Método 1: label com for=id
        if campo.get('id'):
            label = soup.find('label', {'for': campo['id']})
            if label:
                return label.get_text(strip=True)
        
        # Método 2: campo dentro de label
        label_parent = campo.find_parent('label')
        if label_parent:
            return label_parent.get_text(strip=True)
        
        # Método 3: label imediatamente antes
        elemento_anterior = campo.find_previous_sibling(['label'])
        if elemento_anterior and elemento_anterior.name == 'label':
            return elemento_anterior.get_text(strip=True)
        
        return ""
        
    except Exception:
        return ""


def _detectar_acao_botao(texto: str) -> str:
    """
    Detecta a ação provável de um botão baseado no texto.
    
    Args:
        texto (str): Texto do botão
    
    Returns:
        str: Ação provável
    """
    texto_lower = texto.lower().strip()
    
    if any(x in texto_lower for x in ['entrar', 'login', 'acessar']):
        return "login"
    elif any(x in texto_lower for x in ['enviar', 'submit', 'confirmar']):
        return "submit"
    elif any(x in texto_lower for x in ['buscar', 'pesquisar']):
        return "search"
    elif any(x in texto_lower for x in ['próximo', 'continuar']):
        return "next"
    elif any(x in texto_lower for x in ['salvar', 'save']):
        return "save"
    else:
        return "action"


def _detectar_acao_link(texto: str, href: str = '') -> str:
    """
    Detecta a ação provável de um link baseado no texto e href.
    
    Args:
        texto (str): Texto do link
        href (str): URL do link
    
    Returns:
        str: Ação provável
    """
    texto_lower = texto.lower().strip()
    href_lower = href.lower() if href else ''
    
    # Combinar texto e href para análise
    conteudo = f"{texto_lower} {href_lower}"
    
    if any(x in conteudo for x in ['entrar', 'login', 'acessar', 'candidato', 'portal']):
        return "login"
    elif any(x in conteudo for x in ['cadastro', 'registro', 'criar']):
        return "register"
    elif any(x in conteudo for x in ['esqueci', 'recuperar']):
        return "recovery"
    else:
        return "navigate"


def _detectar_contexto_pagina(soup: BeautifulSoup, elementos: List[Dict]) -> str:
    """
    Detecta o contexto/tipo da página baseado nos elementos.
    
    Args:
        soup: BeautifulSoup object
        elementos: Lista de elementos extraídos
    
    Returns:
        str: Contexto da página
    """
    try:
        # Analisar título da página
        titulo = soup.find('title')
        titulo_texto = titulo.get_text().lower() if titulo else ""
        
        # Analisar elementos presentes
        tem_senha = any(el.get('proposito') == 'senha' for el in elementos if el.get('proposito'))
        tem_email = any(el.get('proposito') == 'email' for el in elementos if el.get('proposito'))
        tem_cpf = any(el.get('proposito') == 'cpf' for el in elementos if el.get('proposito'))
        
        # Detectar contexto
        if 'login' in titulo_texto or (tem_email and tem_senha):
            return "login"
        elif 'cadastro' in titulo_texto or 'registro' in titulo_texto:
            return "register"
        elif tem_cpf or 'documento' in titulo_texto:
            return "document"
        elif any('busca' in el.get('proposito', '') for el in elementos):
            return "search"
        else:
            return "general"
            
    except Exception:
        return "unknown"


def _priorizar_elementos(elementos: List[Dict], contexto: str) -> List[Dict]:
    """
    Prioriza elementos baseado no contexto da página.
    
    Args:
        elementos: Lista de elementos
        contexto: Contexto detectado
    
    Returns:
        List[Dict]: Elementos priorizados
    """
    def calcular_prioridade(elemento):
        prioridade = 0
        
        # ALTA PRIORIDADE: Botões submit sempre no topo
        if elemento['tipo'] == 'botao' and elemento.get('tipo_botao') == 'submit':
            prioridade += 50
        
        # ALTA PRIORIDADE: Campos de senha (incluindo repetição)
        if elemento['tipo'] == 'campo' and elemento.get('proposito') == 'senha':
            prioridade += 40
        
        # Prioridade por tipo
        if elemento['tipo'] == 'campo':
            prioridade += 10
        elif elemento['tipo'] == 'botao':
            prioridade += 8
        elif elemento['tipo'] == 'link':
            prioridade += 5
        
        # Prioridade por contexto
        if contexto == "login":
            if elemento.get('proposito') in ['email', 'cpf']:
                prioridade += 15
            elif elemento.get('proposito') == 'senha':
                prioridade += 15
            elif elemento.get('acao_provavel') == 'login':
                prioridade += 12
        
        # Prioridade por obrigatoriedade
        if elemento.get('obrigatorio'):
            prioridade += 5
        
        return prioridade
    
    return sorted(elementos, key=calcular_prioridade, reverse=True)
