"""
Modulo de Geracao de prompts otimizados para LLM.
Centraliza toda logica de construcao de prompts com contexto e historico.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple

from .html_parser import extrair_elementos_interativos_completos, _detectar_contexto_pagina, _priorizar_elementos
from .io import salvar_lista_seletores


def gerar_prompt_em_chat_format(html: str, screenshot_path: Optional[str] = None,
                               instrucoes_customizadas: Optional[str] = None,
                               modelo: str = "qwen/qwen2.5-vl-7b",
                               historico_acoes: Optional[List] = None) -> Tuple[Dict, List[str]]:
    """
    Gera prompt no formato de chat para LLM com analise HTML otimizada.

    Args:
        html (str): HTML da pagina.
        screenshot_path (str, optional): Caminho para screenshot.
        instrucoes_customizadas (str, optional): Instrucoes especificas do usuario.
        modelo (str): Modelo LLM a ser usado.
        historico_acoes (List, optional): Historico de acoes executadas.

    Returns:
        Tuple[Dict, List[str]]: (payload_chat, seletores_validos)

    Fluxo: Funcao principal para geracao de prompts contextualizados.
    """
    # Detectar modelo automaticamente se for o padrao
    if modelo == "qwen/qwen2.5-vl-7b":
        try:
            from .llm import obter_modelo_carregado
            modelo_detectado = obter_modelo_carregado()
            if modelo_detectado:
                modelo = modelo_detectado
                print(f"[INFO] Modelo redirecionado de fallback para detectado: {modelo}")
        except Exception as e:
            print(f"[ALERTA] Erro ao detectar modelo: {e}")
            # Continua com modelo padrao

    try:
        # Parsear HTML e extrair elementos
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extrair elementos interativos (precisa da pagina, usar None como fallback)
        elementos = extrair_elementos_interativos_completos(soup, None)

        # Detectar contexto e priorizar elementos
        contexto = _detectar_contexto_pagina(soup, elementos)
        elementos_priorizados = _priorizar_elementos(elementos, contexto)

        # Limitar elementos para nao sobrecarregar prompt
        elementos_limitados = elementos_priorizados[:30]

        # Gerar lista de seletores validos
        seletores_validos = [el['seletor'] for el in elementos_limitados if el.get('seletor')]

        # Identificar campos preenchidos para marcar na lista
        campos_preenchidos = set()
        if historico_acoes:
            for acao in historico_acoes:
                # Compatibilidade com ambos os formatos (acao/action)
                acao_tipo = acao.get('acao') or acao.get('action')
                if (
                    acao_tipo == 'type'
                    and acao.get('sucesso', False)
                    and (acao.get('seletor') or acao.get('selector'))
                ):
                    seletor = acao.get('seletor') or acao.get('selector')
                    campos_preenchidos.add(seletor)

        # Construir prompt do sistema com status dos campos
        prompt_sistema = _construir_prompt_sistema(contexto, elementos_limitados, campos_preenchidos)

        # Construir contexto da pagina
        contexto_pagina = _construir_contexto_pagina(soup, elementos_limitados, historico_acoes)

        # Construir instrucoes especificas (passa histórico para reforçar objetivo em caso de falhas)
        instrucoes_finais = _construir_instrucoes_finais(instrucoes_customizadas, contexto, historico_acoes)

        # Construir payload do chat
        messages = [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"{contexto_pagina}\n\n{instrucoes_finais}"},
        ]

        # Adicionar screenshot se disponivel e modelo suportar
        if screenshot_path and _modelo_suporta_imagem(modelo):
            try:
                import base64
                import os

                if os.path.exists(screenshot_path):
                    with open(screenshot_path, "rb") as img_file:
                        image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                        messages[-1]["content"] = [
                            {"type": "text", "text": f"{contexto_pagina}\n\n{instrucoes_finais}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ]
            except Exception as e:
                logging.warning(f"Erro ao processar imagem para modelo multimodal: {e}")
                # Fallback para so texto se houver erro com a imagem
                messages[-1]["content"] = f"{contexto_pagina}\n\n{instrucoes_finais}"

        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 2048,
        }

        logging.info(f"Prompt gerado com {len(elementos_limitados)} elementos para contexto '{contexto}'")
        return payload, seletores_validos

    except Exception as e:
        logging.error(f"Erro ao gerar prompt: {e}")
        print(f"[ALERTA] ERRO no gerar_prompt_em_chat_format: {e}")
        print(f"[ALERTA] Usando fallback - prompt basico")
        # Fallback para prompt basico (agora retorna tuple tambem)
        return _gerar_prompt_basico(html, instrucoes_customizadas, modelo, historico_acoes)


def _construir_prompt_sistema(contexto: str, elementos: List[Dict], campos_preenchidos: set = None) -> str:
    """Constroi o prompt do sistema baseado no contexto da pagina"""
    
    if campos_preenchidos is None:
        campos_preenchidos = set()
    
    base_prompt = """Voce e um assistente de automacao web especializado em navegacao e interacao com paginas web.

Sua missao e analisar elementos HTML e decidir a melhor acao para completar uma tarefa especifica.

ALERTA IMPORTANTE: PENALIZACAO SEVERA POR REPETICAO INADEQUADA:
- VOCE SERA PENALIZADO se repetir campos ja preenchidos com sucesso
- VOCE SERA PENALIZADO se ignorar campos obrigatorios como [name='repeatedPassword']
- VOCE SERA PENALIZADO se nao seguir a sequencia logica de preenchimento

REGRAS DE RESPOSTA:
- SEMPRE responda com JSON valido
- Use exatamente esta estrutura: {{"acao": "string", "seletor": "string", "valor": "string", "confianca": number, "justificativa": "string"}}

[CRITICO] FORMATO DE SELETORES CSS - REGRAS ABSOLUTAS:
- Use APENAS seletores CSS PUROS e VALIDOS (sem inventar sintaxe customizada!)
- PROIBIDO usar pipe "|" ou ">>": isso NAO e CSS valido!
- Exemplos de seletores VALIDOS:
  * #login (ID)
  * .btn (classe)
  * [data-testid='auto-area-4'] (atributo)
  * button[type='submit'] (elemento com atributo)
  * .btn.primary (multiplas classes)
- NUNCA invente: ".btn | texto='X'" ou ".btn >> text='X'" - isso e INVALIDO!
- Se precisa de texto especifico, use o seletor exato da lista fornecida
- Quando houver multiplos .btn, escolha o [data-testid] correspondente da lista

ACOES DISPONIVEIS:
- "click": Para clicar em links, botoes, checkboxes
- "type": Para PREENCHER campos de texto/input/password (sempre inclua valor!)
- "submit": APENAS para enviar formularios completos (botoes de envio)
- "scroll": Para rolar a pagina
- "wait": Para aguardar carregamento

FOCO EM CAMPOS DE TEXTO:
- Para preencher campos use apenas acao "type"; o agente executa o clique de foco automaticamente antes de digitar
- NUNCA envie uma acao "click" separada para o mesmo campo que sera preenchido
- Use "click" somente quando o clique for o destino final (navegar, expandir, confirmar)

REGRAS CRITICAS DE PREENCHIMENTO:
- Para PREENCHER campos [name='customer.firstName'] etc: use acao "type" com valor
- CAMPO CRITICO: [name='repeatedPassword'] deve usar o MESMO VALOR da senha anterior
- NUNCA REPITA campos marcados como "JA PREENCHIDO"

EXEMPLO CORRETO para preencher nome:
{{"acao": "type", "seletor": "[name='customer.firstName']", "valor": "Joao Silva", "confianca": 95, "justificativa": "Preenchendo primeiro campo do cadastro"}}

EXEMPLO CORRETO para confirmacao de senha:
{{"acao": "type", "seletor": "[name='repeatedPassword']", "valor": "senha123", "confianca": 95, "justificativa": "Confirmando senha com o mesmo valor usado em customer.password"}}

[AVISO] REGRA ABSOLUTA: NAO REPITA campos ja preenchidos! Procure o PROXIMO campo vazio da sequencia!

CONTEXTO DA PAGINA: {contexto}

ELEMENTOS DISPONIVEIS:"""

    def _format_text(value: Optional[str], limit: int = 50) -> str:
        if not value:
            return "-"
        texto = str(value).strip().replace("\n", " ")
        return texto[:limit]

    elementos_textuais = [
        el for el in elementos
        if el.get('tipo') == 'campo' and (el.get('elemento') or '').lower() in {'input', 'textarea'}
    ]
    inputs_vazios = [
        el for el in elementos_textuais
        if not (el.get('valor_atual') or '').strip() and (el.get('seletor') not in campos_preenchidos)
    ]
    outros_campos_texto = [el for el in elementos_textuais if el not in inputs_vazios]

    elementos_clicaveis = [
        el for el in elementos
        if el.get('tipo') in {'botao', 'botao_role', 'link'}
    ]

    elementos_text_parts = []

    elementos_text_parts.append(f"\n[CAMPOS DE INPUT VAZIOS: {len(inputs_vazios)}]")
    if inputs_vazios:
        for el in inputs_vazios[:10]:
            seletor = el.get('seletor', 'N/A')
            label = _format_text(el.get('label'), 40)
            placeholder = _format_text(el.get('placeholder'), 40)
            proposito = _format_text(el.get('proposito') or el.get('tipo_campo'), 25)
            elementos_text_parts.append(
                f" - {seletor} | label='{label}' | placeholder='{placeholder}' | tipo={proposito}"
            )
        if len(inputs_vazios) > 10:
            elementos_text_parts.append(f"   ... {len(inputs_vazios) - 10} campos adicionais ocultos")
    else:
        elementos_text_parts.append(" - Nenhum campo vazio encontrado")

    if outros_campos_texto:
        elementos_text_parts.append(f"\n[OUTROS CAMPOS DE TEXTO: {len(outros_campos_texto)}]")
        for el in outros_campos_texto[:10]:
            seletor = el.get('seletor', 'N/A')
            label = _format_text(el.get('label'), 40)
            placeholder = _format_text(el.get('placeholder'), 40)
            valor_atual = _format_text(el.get('valor_atual'), 35)
            status = " [OK] JA PREENCHIDO" if seletor in campos_preenchidos or el.get('preenchido') else ""
            elementos_text_parts.append(
                f" - {seletor} | atual='{valor_atual}' | label='{label}' | placeholder='{placeholder}'{status}"
            )
        if len(outros_campos_texto) > 10:
            elementos_text_parts.append(f"   ... {len(outros_campos_texto) - 10} campos adicionais ocultos")

    elementos_text_parts.append(f"\n[AREAS CLICAVEIS RELEVANTES: {len(elementos_clicaveis)}]")
    if elementos_clicaveis:
        # Detectar multiplos elementos com mesma classe/seletor (ex: .btn, .btn.btn-primary)
        seletores_duplicados = {}
        for el in elementos_clicaveis:
            seletor = el.get('seletor', '')
            # Detectar seletores baseados em classe (com ou sem combinações)
            if seletor.startswith('.') and not '[' in seletor:  
                seletores_duplicados[seletor] = seletores_duplicados.get(seletor, 0) + 1
        
        tem_duplicados = any(count > 1 for count in seletores_duplicados.values())
        if tem_duplicados:
            elementos_text_parts.append("\n⚠️ [ALERTA] Ha multiplos elementos com mesma classe (ex: .btn, .nav-link)")
            elementos_text_parts.append("   SEMPRE prefira seletores [data-testid='...'] para evitar ambiguidade!\n")
        
        for el in elementos_clicaveis[:10]:
            seletor = el.get('seletor', 'N/A')
            texto = _format_text(el.get('texto') or el.get('label'), 50)
            tipo = (el.get('tipo') or el.get('elemento') or 'N/A').upper()
            
            # FORMATO CLARO: Seletor primeiro, depois texto entre parênteses
            # Exemplo: .btn.btn-primary (texto: "Entrar")
            elementos_text_parts.append(
                f" - {seletor} → {tipo} com texto=\"{texto}\""
            )
        if len(elementos_clicaveis) > 10:
            elementos_text_parts.append(f"   ... {len(elementos_clicaveis) - 10} elementos clicaveis adicionais ocultos")
    else:
        elementos_text_parts.append(" - Nenhum elemento clicavel relevante encontrado")

    elementos_text = "".join(elementos_text_parts)

    return base_prompt.format(contexto=contexto) + elementos_text


def _construir_contexto_pagina(soup: Any, elementos: List[Dict], historico: Optional[List] = None) -> str:
    """Constroi contexto atual da pagina"""

    title = soup.find('title')
    title_text = title.get_text() if title else "Sem titulo"

    contexto = f"PAGINA ATUAL: {title_text}\n"
    contexto += f"ELEMENTOS INTERATIVOS ENCONTRADOS: {len(elementos)}\n"

    if historico:
        contexto += f"\nHISTORICO DE ACOES ({len(historico)} acoes):\n"
        acoes_repetidas = 0
        campos_preenchidos = set()
        elementos_invisiveis = set()

        # Identificar campos ja preenchidos com sucesso e elementos invisíveis
        for acao in historico:
            # Compatibilidade com ambos os formatos (acao/action)
            acao_tipo = acao.get('acao') or acao.get('action')
            seletor = acao.get('seletor') or acao.get('selector')
            mensagem_erro = acao.get('mensagem', '')
            
            # Campos preenchidos com sucesso
            if (
                acao_tipo == 'type'
                and acao.get('sucesso', False)
                and seletor
            ):
                campos_preenchidos.add(seletor)
            
            # Elementos que falharam por invisibilidade
            if not acao.get('sucesso', False) and 'ELEMENTO_INVISIVEL' in mensagem_erro:
                elementos_invisiveis.add(seletor)

        # Mostrar historico de todas as acoes (sem limitacao)
        for i, acao in enumerate(historico, 1):
            acao_tipo = acao.get('acao') or acao.get('action')
            acao_texto = acao_tipo or 'N/A'
            seletor = acao.get('seletor', 'N/A')
            sucesso = acao.get('sucesso', False)
            mensagem = acao.get('mensagem', '')
            
            status = "[OK] SUCESSO" if sucesso else "[ERRO] FALHOU"
            motivo_falha = ""
            
            if acao.get('repetida', False):
                acoes_repetidas += 1
                status += " (REPETIDA)"
            
            # Adicionar detalhes específicos da falha
            if not sucesso:
                if 'ELEMENTO_INVISIVEL' in mensagem:
                    status += " - ELEMENTO OCULTO"
                    motivo_falha = " | Motivo: Elemento existe mas está invisível no DOM"
                elif 'strict mode violation' in mensagem:
                    status += " - SELETOR AMBIGUO"
                    motivo_falha = " | Motivo: Seletor retornou múltiplos elementos, seja mais específico"
                elif 'Timeout' in mensagem or 'timeout' in mensagem:
                    status += " - TIMEOUT"
                    motivo_falha = " | Motivo: Elemento não foi encontrado no tempo limite"
                elif 'not found' in mensagem.lower():
                    status += " - NAO ENCONTRADO"
                    motivo_falha = " | Motivo: Elemento não existe na página"
                elif mensagem:
                    motivo_falha = f" | Motivo: {mensagem[:80]}"
            
            contexto += f"{i}. {acao_texto} em {seletor} - {status}{motivo_falha}\n"

        # Informar sobre campos preenchidos
        if campos_preenchidos:
            contexto += f"\n[OK] CAMPOS JA PREENCHIDOS ({len(campos_preenchidos)}):\n"
            for campo in sorted(campos_preenchidos):
                contexto += f"   - {campo}\n"
            
            contexto += "\n[REGRA] NAO REPITA campos ja preenchidos!\n"
            contexto += "[FOCO] Analise os elementos disponiveis e escolha o proximo campo vazio mais relevante.\n"
        
        # Informar sobre elementos invisíveis
        if elementos_invisiveis:
            contexto += f"\n[ALERTA] ELEMENTOS INVISIVEIS/OCULTOS ({len(elementos_invisiveis)}):\n"
            for elemento in sorted(elementos_invisiveis):
                contexto += f"   - {elemento} - EXISTE mas está OCULTO na página\n"
            
            contexto += "\n[INSTRUCAO CRITICA] Os elementos acima estão OCULTOS/INVISIVEIS!\n"
            contexto += "- NAO tente clicar nestes elementos novamente\n"
            contexto += "- Procure seletores ALTERNATIVOS na lista disponível\n"
            contexto += "- Elementos duplicados (ex: auto-area-do-candidato-4 vs auto-area-do-candidato-10) podem ter visibilidades diferentes\n"
            contexto += "- Tente o próximo elemento similar ou use outro caminho para atingir o objetivo\n"

        if acoes_repetidas > 0:
            contexto += f"\n[AVISO] {acoes_repetidas} das ultimas acoes foram repetidas. "
            contexto += "Considere tentar seletores diferentes ou acoes alternativas para progredir.\n"
            contexto += "\n[IMPORTANTE] Sua ultima tentativa NAO funcionou. Voce DEVE tentar uma abordagem DIFERENTE.\n"
            contexto += "Analise os elementos disponiveis e escolha um seletor ALTERNATIVO mais especifico.\n"

    return contexto


def _construir_instrucoes_finais(instrucoes_custom: Optional[str], contexto: str, historico: Optional[list] = None) -> str:
    """Constroi instrucoes finais baseadas no contexto"""

    if instrucoes_custom:
        base_instruction = f"TAREFA ESPECIFICA: {instrucoes_custom}\n\n"

        # Adicionar dicas genericas
        base_instruction += """DIRETRIZES GERAIS:

- Consulte a secao de ELEMENTOS listados no prompt do sistema.
- Avalie cada elemento disponivel e decida qual faz sentido para a tarefa atual.
- Para preencher campos use acao "type" com um valor apropriado (o agente fara o foco automaticamente).
- Para navegar ou confirmar use acao "click" no elemento apropriado.
- NUNCA repita campos ja marcados como preenchidos.
- Use os rotulos, placeholders e contexto da pagina para decidir valores apropriados.
- Para formularios, preencha campos de texto com dados fake realistas e coerentes.

"""
        
        # Se houver falhas no histórico, reforçar o objetivo
        if historico and len(historico) > 0:
            tem_falhas = any(not acao.get('sucesso', False) for acao in historico)
            acoes_recentes_falharam = len(historico) >= 2 and all(
                not acao.get('sucesso', False) for acao in historico[-2:]
            )
            
            if acoes_recentes_falharam:
                base_instruction += f"\n[ATENCAO] Suas ultimas tentativas falharam!\n"
                base_instruction += f"LEMBRE-SE DO SEU OBJETIVO PRINCIPAL: {instrucoes_custom}\n"
                base_instruction += "Voce PRECISA encontrar uma forma DIFERENTE de atingir este objetivo.\n"
                base_instruction += "Tente seletores mais especificos (com data-testid, #id ou classes unicas).\n\n"
            elif tem_falhas:
                base_instruction += f"\n[LEMBRETE] SEU OBJETIVO PRINCIPAL: {instrucoes_custom}\n\n"

        return base_instruction + "Analise os elementos disponiveis e selecione a proxima acao mais logica para completar a tarefa."

    # Instrucoes baseadas no contexto
    if "login" in contexto.lower():
        return "Identifique campos de login (email/usuario e senha) e botao de submit. Use dados fake apropriados."
    elif "formulario" in contexto.lower() or "register" in contexto.lower():
        return "Analise os campos do formulario e preencha com dados fake apropriados, depois submeta quando todos os campos relevantes estiverem completos."
    else:
        return "Analise a pagina e identifique a proxima acao mais logica para navegar ou interagir com o conteudo."


def _extrair_identificador_campo(seletor: Optional[str]) -> Optional[str]:
    """Extrai um identificador normalizado a partir de diferentes formatos de seletor."""
    if not seletor:
        return None

    texto = seletor.strip()
    texto_lower = texto.lower()

    def _limpar(valor: str) -> str:
        return valor.strip("'\" ").lower()

    for chave in ("[name=", "[id=", "[data-testid=", "[data-test=", "[aria-label="):
        if chave in texto_lower:
            inicio = texto_lower.index(chave) + len(chave)
            fim = texto_lower.find("]", inicio)
            if fim != -1:
                return _limpar(texto_lower[inicio:fim])

    if texto_lower.startswith("#"):
        return texto_lower[1:].split()[0]

    if texto_lower.startswith("."):
        return texto_lower[1:].split()[0]

    if "[type=" in texto_lower:
        inicio = texto_lower.index("[type=") + len("[type=")
        fim = texto_lower.find("]", inicio)
        if fim != -1:
            return _limpar(texto_lower[inicio:fim])

    identificado = re.sub(r"[^a-z0-9._-]", "", texto_lower)
    return identificado or texto_lower


def _modelo_suporta_imagem(modelo: str) -> bool:
    """Verifica se o modelo suporta imagens"""
    if not modelo:
        return False
        
    modelo_lower = modelo.lower()
    
    # Lista mais completa e precisa de modelos com visao
    modelos_com_visao = [
        "qwen2.5-vl", "qwen-vl", "qwen2-vl",  # Familia Qwen VL
        "llava", "llava-1.5", "llava-1.6",   # Familia LLaVA
        "gpt-4-vision", "gpt-4v", "gpt-4-turbo-vision",  # OpenAI Vision
        "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash",  # Google Vision
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",  # Anthropic Vision
        "minicpm-v", "internvl", "idefics", "kosmos", "cogvlm", "blip"  # Outros
    ]
    
    return any(visao in modelo_lower for visao in modelos_com_visao)


def _gerar_prompt_basico(html: str, instrucoes: Optional[str], modelo: str, historico_acoes: Optional[List] = None) -> Tuple[Dict, List[str]]:
    """Fallback para prompt basico quando ha erro na analise"""
    
    # Extrair apenas o body e encontrar elementos basicos
    from bs4 import BeautifulSoup
    elementos_encontrados = []
    seletores_validos = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Encontrar elementos interativos basicos
        for input_elem in soup.find_all(['input', 'button', 'a', 'select', 'textarea']):
            seletor = ""
            texto = ""
            
            # Gerar seletor simples
            if input_elem.get('id'):
                seletor = f"#{input_elem['id']}"
            elif input_elem.get('name'):
                seletor = f"[name='{input_elem['name']}']"
            elif input_elem.get('data-testid'):
                seletor = f"[data-testid='{input_elem['data-testid']}']"
            elif input_elem.get('class'):
                classes = ' '.join(input_elem['class'][:2])  # Primeiras 2 classes
                seletor = f".{classes.replace(' ', '.')}"
            else:
                seletor = input_elem.name
            
            # Obter texto do elemento
            if input_elem.name == 'input':
                texto = input_elem.get('placeholder', '') or input_elem.get('value', '') or input_elem.get('type', 'text')
            else:
                texto = input_elem.get_text(strip=True)[:30]
            
            if seletor and (texto or input_elem.name in ['button', 'input']):
                elementos_encontrados.append(f"{input_elem.name.upper()}: {seletor} - {texto}")
                seletores_validos.append(seletor)
        
        # Usar body se possivel
        body = soup.find('body')
        if body:
            title = soup.find('title')
            title_text = title.get_text() if title else 'Sem titulo'
            html_relevante = f"<title>{title_text}</title>\n{str(body)[:6000]}"
        else:
            html_relevante = html[:6000]
            
    except Exception as e:
        print(f"[ALERTA] Erro ao analisar HTML basico: {e}")
        html_relevante = html[:6000]
        elementos_encontrados = ["ERRO: Nao foi possivel analisar elementos"]
    
    # Identificar campos ja preenchidos do historico
    campos_preenchidos = set()
    if historico_acoes:
        for acao in historico_acoes:
            # Compatibilidade com ambos os formatos (acao/action)
            acao_tipo = acao.get('acao') or acao.get('action')
            if (acao_tipo == 'type' and 
                acao.get('sucesso', False) and 
                (acao.get('seletor') or acao.get('selector'))):
                seletor = acao.get('seletor') or acao.get('selector')
                campos_preenchidos.add(seletor)

    campos_preenchidos_identidades = {
        _extrair_identificador_campo(sel) for sel in campos_preenchidos if sel
    }

    # Detectar campos de formulario apenas genericamente (sem hardcode de nomes especificos)
    campos_status = []
    for seletor in seletores_validos:
        ident = _extrair_identificador_campo(seletor)
        # Incluir apenas inputs de formulario (excluir botoes e links)
        if ident and any(indicador in seletor.lower() for indicador in ['[name=', 'input', 'textarea', 'select']):
            if '[type=' in seletor.lower() and any(tipo in seletor.lower() for tipo in ['submit', 'button']):
                continue  # Pular botoes
            status_atual = "[OK] JA FEITO" if ident in campos_preenchidos_identidades else "[PENDENTE]"
            campos_status.append((seletor, status_atual, ident))
    
    # Marcar elementos ja preenchidos na lista
    elementos_marcados = []
    for elemento in elementos_encontrados:
        marcado = elemento
        # Verificar se algum seletor preenchido esta no elemento
        for campo in campos_preenchidos:
            if campo in elemento:
                marcado += " [OK] JA PREENCHIDO"
                break
        elementos_marcados.append(marcado)
    
    elementos_texto = "\n".join(elementos_marcados[:10])  # Limitar a 10 elementos
    
    prompt = f"""Analise este HTML e responda com JSON no formato exato:
{{"acao": "string", "seletor": "string", "valor": "string", "confianca": number, "justificativa": "string"}}

ELEMENTOS INTERATIVOS ENCONTRADOS:
{elementos_texto}

HTML da pagina ({len(html_relevante)} chars):
{html_relevante}

Instrucoes: {instrucoes or 'Identifique elementos interativos e a proxima acao logica'}

HISTORICO DE PROGRESSO:"""
    
    # Adicionar informacoes sobre campos preenchidos
    if campos_preenchidos:
        prompt += f"""
[OK] CAMPOS JA PREENCHIDOS ({len(campos_preenchidos)}):"""
        for campo in sorted(campos_preenchidos):
            prompt += f"""
   - {campo}"""
        prompt += """

[REGRA] NAO REPITA campos ja preenchidos!
[FOCO] Escolha o proximo campo vazio mais relevante para a tarefa."""
    
    # Adicionar sequencia de campos com status dinamico somente para campos detectados
    if campos_status:
        prompt += "\n\nCAMPOS DETECTADOS NA PAGINA:"
        for i, (seletor_display, status_atual, _) in enumerate(campos_status, 1):
            prompt += f"\n{i}. {seletor_display} <- {status_atual}"
    
    prompt += """

REGRAS DE ACOES:
- "click": Para clicar em links, botoes, checkboxes (quando o clique for a acao final)
- "type": Para PREENCHER campos de texto (input, textarea) com valores apropriados
- "submit": APENAS para enviar formularios completos
- "scroll": Para rolar a pagina
- "wait": Para aguardar carregamento

IMPORTANTE: 
- Use APENAS seletores dos ELEMENTOS ENCONTRADOS acima
- COPIE o seletor EXATAMENTE como aparece na lista
- Para preencher campos use acao "type" com valor apropriado (o agente fara o foco automaticamente)
- NAO repita campos ja preenchidos
- Gere dados fake realistas e coerentes com o contexto do campo
- Responda APENAS com JSON valido: {"acao": "...", "seletor": "...", "valor": "...", "confianca": N, "justificativa": "..."}"""
    
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,  # Aumentado para ser mais criativo e menos determinístico
        "max_tokens": 1024
    }
    
    return payload, seletores_validos[:20]  # Limitar seletores


def otimizar_payload_para_modelo(payload: Dict, modelo: str) -> Dict:
    """Otimiza payload especifico para cada modelo."""

    if "qwen" in modelo.lower():
        payload["temperature"] = 0.3  # Aumentado para mais variabilidade
        payload["top_p"] = 0.9
    elif "gemma" in modelo.lower():
        payload["temperature"] = 0.3  # Aumentado para evitar repetições
        payload["top_k"] = 40
    elif "llama" in modelo.lower():
        payload["temperature"] = 0.4  # Aumentado para mais criatividade
        payload["repeat_penalty"] = 1.1

    return payload


def extrair_elementos_otimizados_llm(pagina):
    """Extrai elementos otimizados da pagina para LLM."""
    try:
        from bs4 import BeautifulSoup
        from .html_parser import extrair_elementos_interativos_completos

        soup = BeautifulSoup(pagina.content(), 'html.parser')
        elementos = extrair_elementos_interativos_completos(soup, pagina)

        return {
            'elementos': elementos[:20],
            'html': str(soup)[:5000],
            'title': soup.find('title').get_text() if soup.find('title') else 'Sem titulo',
        }
    except Exception as e:
        logging.error(f"Erro ao extrair elementos: {e}")
        return {'elementos': [], 'html': '', 'title': 'Erro na extracao'}


def gerar_prompt_autonomo_completo(html_content, screenshot_path=None, instrucoes_customizadas=None,
                                   modelo="qwen/qwen2.5-vl-7b", historico_acoes=None, pagina=None):
    """Gera prompt autonomo completo - wrapper para compatibilidade."""
    return gerar_prompt_em_chat_format(
        html=html_content,
        screenshot_path=screenshot_path,
        instrucoes_customizadas=instrucoes_customizadas,
        modelo=modelo,
        historico_acoes=historico_acoes,
    )


def gerar_instrucoes_contextuais(elementos: List[Dict], contexto: str) -> str:
    """Gera instrucoes contextuais baseadas nos elementos encontrados"""
    
    if not elementos:
        return "Nao foram encontrados elementos interativos na pagina."
    
    tipos_elementos = {}
    for el in elementos:
        tag = el.get('tag', 'unknown')
        tipos_elementos[tag] = tipos_elementos.get(tag, 0) + 1

    instrucoes = f"Encontrados {len(elementos)} elementos interativos:\n"
    for tag, count in tipos_elementos.items():
        instrucoes += f"- {count} {tag}(s)\n"

    if contexto == "login":
        instrucoes += "\nSugestao: Procure por campos 'email', 'password' e botao 'submit'"
    elif contexto == "formulario":
        instrucoes += "\nSugestao: Complete campos obrigatorios (*) antes de submeter"
    elif contexto == "navegacao":
        instrucoes += "\nSugestao: Procure por links ou botoes de navegacao"

    return instrucoes


def validar_seletor_e_retry(resposta_llm, seletores_validos, func_chamar_llm, payload_original):
    """Valida seletor e faz retry se necessario"""
    try:
        import json
        from .validation import validar_resposta_llm, validar_seletor_existente
        
        # Limpar markdown se presente
        resposta_limpa = resposta_llm
        if resposta_limpa.startswith('```json'):
            resposta_limpa = resposta_limpa.replace('```json', '').replace('```', '').strip()
        elif resposta_limpa.startswith('```'):
            resposta_limpa = resposta_limpa.replace('```', '').strip()
        
        print(f"[DEBUG] Validando resposta: {resposta_limpa[:100]}...")
        print(f"[DEBUG] Seletores validos disponiveis: {len(seletores_validos)} itens")
        
        # Tentar validar resposta (retorna tupla: valido, dados, motivo)
        valido, acao_data, motivo = validar_resposta_llm(resposta_limpa)
        
        if valido and acao_data:
            seletor = acao_data.get('seletor') or acao_data.get('selector')
            
            # Usar validacao flexivel em vez de verificacao simples
            valido_seletor, motivo_seletor = validar_seletor_existente(seletor, seletores_validos)
            
            if valido_seletor:
                print(f"[OK] Seletor '{seletor}' valido! ({motivo_seletor})")
                return acao_data
            
            # Retry com correcao de seletor
            logging.warning(f"Seletor invalido: {seletor}, tentando correcao...")
            payload_retry = payload_original.copy()
            payload_retry['messages'].append({
                "role": "user", 
                "content": f"O seletor '{seletor}' nao e valido. Seletores disponiveis: {seletores_validos[:5]}. Corrija sua resposta."
            })
            
            resposta_retry = func_chamar_llm(payload_retry)
            resposta_retry_limpa = resposta_retry.replace('```json', '').replace('```', '').strip()
            
            valido_retry, acao_retry, motivo_retry = validar_resposta_llm(resposta_retry_limpa)
            if valido_retry and acao_retry:
                seletor_retry = acao_retry.get('seletor') or acao_retry.get('selector')
                valido_seletor_retry, motivo_seletor_retry = validar_seletor_existente(seletor_retry, seletores_validos)
                if valido_seletor_retry:
                    return acao_retry
                    
        else:
            print(f"[ERRO] [VALIDACAO] Resposta nao passou na validacao basica: {motivo}")
                
        return None
        
    except Exception as e:
        logging.error(f"Erro na validacao: {e}")
        print(f"[DEBUG] [DEBUG] Erro na validacao: {e}")
        return None


def gerar_prompt_otimizado_com_contexto(navegacao_llm, instrucoes_customizadas, historico_acoes, modelo):
    """Gera prompt otimizado com contexto - wrapper para compatibilidade"""
    return gerar_prompt_em_chat_format(
        html=navegacao_llm.get('html', ''),
        instrucoes_customizadas=instrucoes_customizadas,
        historico_acoes=historico_acoes,
        modelo=modelo
    )
