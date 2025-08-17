"""
Modulo de Geracao de prompts otimizados para LLM
Centraliza toda logica de construcao de prompts com contexto e historico.

Fluxo de Execucao    elementos_text = ""
    for i, el in enumerate(elementos, 1):
        seletor = el.get('seletor', 'N/A')
        status = ""
        
        # Marcar campos ja preenchidos de forma mais visivel
        if seletor in campos_preenchidos:
            status = " [OK] JA PREENCHIDO"
        else:
            # Verificação mais inteligente - comparar também por name e id
            campo_preenchido = False
            for campo_hist in campos_preenchidos:
                # Remover # se presente para comparar
                campo_limpo = campo_hist.replace('#', '') if campo_hist.startswith('#') else campo_hist
                
                # Verificar se o seletor atual corresponde ao campo do histórico
                if (campo_limpo in seletor or  # Ex: firstName em [name='firstName']
                    seletor.replace("[name='", "").replace("']", "") in campo_limpo or  # Ex: firstName em customer.firstName
                    campo_limpo.split('.')[-1] in seletor):  # Ex: firstName (última parte) em [name='firstName']
                    campo_preenchido = True
                    status = " [OK] JA PREENCHIDO"
                    break
            
            if not campo_preenchido and el.get('tag') == 'INPUT' and any(campo in seletor for campo in ['firstName', 'lastName', 'customer']):
                status = " [ACAO] AGUARDANDO PREENCHIMENTO"
            
        elementos_text += f"\n{i}. {el.get('tag', 'N/A')} - {seletor} - {el.get('texto', 'N/A')[:50]}{status}"
    
    # Adicionar seção especial para campos preenchidos se houver
    if campos_preenchidos:
        elementos_text += f"\n\n[ALERTA] CAMPOS JA PREENCHIDOS ({len(campos_preenchidos)}):\n"
        for campo in sorted(campos_preenchidos):
            elementos_text += f"   - {campo}\n"
        elementos_text += "\n[ALERTA] CRITICO: NAO REPITA campos ja preenchidos!\n"
        elementos_text += "[FOCO] PROXIMA ACAO OBRIGATORIA: Escolha o PROXIMO campo vazio da sequencia!\n"
        elementos_text += "[PROIBIDO] Usar seletores ja preenchidos acima!\n"
        elementos_text += "\n[FOCO] SEQUENCIA OBRIGATORIA DE PREENCHIMENTO:\n"
        
        # Adicionar sequência de campos com status dinâmico
        campos_sequencia = [
            "#customer.firstName",
            "#customer.lastName", 
            "#customer.address.street",
            "#customer.address.city",
            "#customer.address.state"
        ]
        
        for i, campo in enumerate(campos_sequencia, 1):
            status_campo = "[OK] JA FEITO" if campo in campos_preenchidos else "[ACAO] FAZER AGORA"
            elementos_text += f"{i}. {campo} <- {status_campo}\n"
    
    return base_prompt.format(contexto=contexto) + elementos_textML e elementos extraidos
- Gera prompt contextualizado
- Adiciona historico de acoes
- Otimiza para modelo especifico
- Formata em chat format
"""
import logging
import json
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
        html (str): HTML da pagina
        screenshot_path (str, optional): Caminho para screenshot
        instrucoes_customizadas (str, optional): Instrucoes especificas do usuario
        modelo (str): Modelo LLM a ser usado
        historico_acoes (List, optional): Historico de acoes executadas
    
    Returns:
        Tuple[Dict, List[str]]: (payload_chat, seletores_validos)
    
    Fluxo: Funcao principal para geracao de prompts contextualizados
    """
    # Detectar modelo automaticamente se for o padrao
    if modelo == "qwen/qwen2.5-vl-7b":
        try:
            from .llm import obter_modelo_carregado
            modelo_detectado = obter_modelo_carregado()
            if modelo_detectado:
                modelo = modelo_detectado
                print(f"🔄 Modelo redirecionado de fallback para detectado: {modelo}")
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelo: {e}")
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
        
        # Limitar elementos para nao sobrecarregar prompt - AUMENTADO para capturar mais elementos
        elementos_limitados = elementos_priorizados[:30]  # Aumentado de 20 para 30
        
        # Gerar lista de seletores validos
        seletores_validos = [el['seletor'] for el in elementos_limitados if el.get('seletor')]
        
        # Identificar campos preenchidos para marcar na lista
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
        
        # Construir prompt do sistema com status dos campos
        prompt_sistema = _construir_prompt_sistema(contexto, elementos_limitados, campos_preenchidos)
        
        # Construir contexto da pagina
        contexto_pagina = _construir_contexto_pagina(soup, elementos_limitados, historico_acoes)
        
        # Construir instrucoes especificas
        instrucoes_finais = _construir_instrucoes_finais(instrucoes_customizadas, contexto)
        
        # Construir payload do chat
        messages = [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"{contexto_pagina}\n\n{instrucoes_finais}"}
        ]
        
        # Adicionar screenshot se disponivel e modelo suportar
        if screenshot_path and _modelo_suporta_imagem(modelo):
            messages[-1]["content"] = [
                {"type": "text", "text": f"{contexto_pagina}\n\n{instrucoes_finais}"},
                {"type": "image_url", "image_url": {"url": f"file://{screenshot_path}"}}
            ]
        
        payload = {
            "model": modelo,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 2048
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

🚨 PENALIZAÇÃO SEVERA POR REPETIÇÃO INADEQUADA:
- VOCÊ SERÁ PENALIZADO se repetir campos já preenchidos com sucesso
- VOCÊ SERÁ PENALIZADO se ignorar campos obrigatórios como [name='repeatedPassword']
- VOCÊ SERÁ PENALIZADO se não seguir a sequência lógica de preenchimento

REGRAS DE RESPOSTA:
- SEMPRE responda com JSON valido
- Use exatamente esta estrutura: {{"acao": "string", "seletor": "string", "valor": "string", "confianca": number, "justificativa": "string"}}

ACOES DISPONIVEIS:
- "click": Para clicar em links, botoes, checkboxes
- "type": Para PREENCHER campos de texto/input/password (sempre inclua valor!)
- "submit": APENAS para enviar formularios completos (botoes de envio)
- "scroll": Para rolar a pagina
- "wait": Para aguardar carregamento

🔥 REGRAS CRÍTICAS DE PREENCHIMENTO:
- Para PREENCHER campos [name='customer.firstName'] etc: use acao "type" com valor
- Para CLICAR em botoes: use acao "click"
- NUNCA use "click" para preencher campos de input!
- CAMPO CRÍTICO: [name='repeatedPassword'] deve usar o MESMO VALOR da senha anterior
- NUNCA REPITA campos marcados como "JÁ PREENCHIDO"

EXEMPLO CORRETO para preencher nome:
{{"acao": "type", "seletor": "[name='customer.firstName']", "valor": "Joao Silva", "confianca": 95, "justificativa": "Preenchendo primeiro campo do cadastro"}}

EXEMPLO CORRETO para confirmação de senha:
{{"acao": "type", "seletor": "[name='repeatedPassword']", "valor": "senha123", "confianca": 95, "justificativa": "Confirmando senha com o mesmo valor usado em customer.password"}}

⚠️ REGRA ABSOLUTA: NAO REPITA campos ja preenchidos! Procure o PROXIMO campo vazio da sequência!

CONTEXTO DA PAGINA: {contexto}

ELEMENTOS DISPONIVEIS:"""
    
    elementos_text = ""
    for i, el in enumerate(elementos[:15], 1):
        seletor = el.get('seletor', 'N/A')
        status = ""
        
        # Marcar campos ja preenchidos
        if seletor in campos_preenchidos:
            status = " [OK] JÁ PREENCHIDO"
        elif el.get('tag') == 'INPUT' and any(campo in seletor for campo in ['firstName', 'lastName', 'customer']):
            status = " [ACAO] AGUARDANDO PREENCHIMENTO"
            
        elementos_text += f"\n{i}. {el.get('tag', 'N/A')} - {seletor} - {el.get('texto', 'N/A')[:50]}{status}"
    
    return base_prompt.format(contexto=contexto) + elementos_text


def _construir_contexto_pagina(soup: Any, elementos: List[Dict], historico: Optional[List] = None) -> str:
    """Constroi contexto atual da pagina"""
    
    title = soup.find('title')
    title_text = title.get_text() if title else "Sem titulo"
    
    contexto = f"PÁGINA ATUAL: {title_text}\n"
    contexto += f"ELEMENTOS INTERATIVOS ENCONTRADOS: {len(elementos)}\n"
    
    if historico:
        contexto += f"\nHISTÓRICO DE AÇÕES ({len(historico)} acoes):\n"
        acoes_repetidas = 0
        campos_preenchidos = set()
        
        # Identificar campos ja preenchidos com sucesso
        for acao in historico:
            # Compatibilidade com ambos os formatos (acao/action)
            acao_tipo = acao.get('acao') or acao.get('action')
            if (acao_tipo == 'type' and 
                acao.get('sucesso', False) and 
                (acao.get('seletor') or acao.get('selector'))):
                seletor = acao.get('seletor') or acao.get('selector')
                campos_preenchidos.add(seletor)
        
        # Mostrar historico de todas as acoes (sem limitacao)
        for i, acao in enumerate(historico, 1):  # Todas as ações do histórico
            acao_tipo = acao.get('acao') or acao.get('action')
            acao_texto = acao_tipo or 'N/A'
            seletor = acao.get('seletor', 'N/A')
            sucesso = acao.get('sucesso', False)
            status = "[OK] SUCESSO" if sucesso else "[ERRO] FALHOU"
            if acao.get('repetida', False):
                acoes_repetidas += 1
                status += " (REPETIDA)"
            contexto += f"{i}. {acao_texto} em {seletor} - {status}\n"
        
        # Informar sobre campos preenchidos
        if campos_preenchidos:
            contexto += f"\n[OK] CAMPOS JÁ PREENCHIDOS ({len(campos_preenchidos)}):\n"
            for campo in sorted(campos_preenchidos):
                contexto += f"   • {campo}\n"
            
            # Listar campos pendentes explicitamente
            campos_formulario = [
                '[name=\'customer.firstName\']',
                '[name=\'customer.lastName\']', 
                '[name=\'customer.address.street\']',
                '[name=\'customer.address.city\']',
                '[name=\'customer.address.state\']',
                '[name=\'customer.address.zipCode\']',
                '[name=\'customer.phoneNumber\']',
                '[name=\'customer.ssn\']',
                '[name=\'customer.username\']',
                '[name=\'customer.password\']',
                '[name=\'repeatedPassword\']'
            ]
            
            campos_pendentes = [campo for campo in campos_formulario if campo not in campos_preenchidos]
            
            if campos_pendentes:
                contexto += f"\n🎯 CAMPOS PENDENTES ({len(campos_pendentes)}) - PREENCHA UM DESTES:\n"
                for campo in campos_pendentes:
                    if campo == '[name=\'customer.firstName\']':
                        contexto += f"   → {campo} (usar valor: 'Joao Silva')\n"
                    elif campo == '[name=\'customer.lastName\']':
                        contexto += f"   → {campo} (usar valor: 'Silva')\n"
                    elif campo == '[name=\'customer.address.street\']':
                        contexto += f"   → {campo} (usar valor: 'Rua das Flores, 123')\n"
                    elif campo == '[name=\'customer.address.city\']':
                        contexto += f"   → {campo} (usar valor: 'Sao Paulo')\n"
                    elif campo == '[name=\'customer.address.state\']':
                        contexto += f"   → {campo} (usar valor: 'SP')\n"
                    elif campo == '[name=\'customer.address.zipCode\']':
                        contexto += f"   → {campo} (usar valor: '01234-567')\n"
                    elif campo == '[name=\'customer.phoneNumber\']':
                        contexto += f"   → {campo} (usar valor: '11999999999')\n"
                    elif campo == '[name=\'customer.ssn\']':
                        contexto += f"   → {campo} (usar valor: '123456789') ⚠️ OBRIGATÓRIO\n"
                    elif campo == '[name=\'customer.username\']':
                        contexto += f"   → {campo} (usar valor: 'joao123')\n"
                    elif campo == '[name=\'customer.password\']':
                        contexto += f"   → {campo} (usar valor: 'senha123')\n"
                    elif campo == '[name=\'repeatedPassword\']':
                        contexto += f"   → {campo} (usar valor: 'senha123') 🔑 CRÍTICO\n"
                    else:
                        contexto += f"   → {campo}\n"
            
            # LÓGICA INTELIGENTE: Se customer.password foi preenchido, FORCE repeatedPassword
            tem_password = any('customer.password' in campo for campo in campos_preenchidos)
            tem_repeated = any('repeatedPassword' in campo for campo in campos_preenchidos)
            
            if tem_password and not tem_repeated:
                contexto += "\n🚨 PRIORIDADE MÁXIMA: customer.password foi preenchido!\n"
                contexto += "🎯 PRÓXIMA AÇÃO OBRIGATÓRIA: Preencher [name='repeatedPassword'] com \"senha123\"\n"
                contexto += "⚠️ PENALIZAÇÃO SEVERA se ignorar esta sequência crítica!\n"
                contexto += "\n💡 USE EXATAMENTE: {\"acao\": \"type\", \"seletor\": \"[name='repeatedPassword']\", \"valor\": \"senha123\"}\n"
            elif campos_pendentes:
                contexto += f"\n[FOCO] PRÓXIMA AÇÃO: Escolha o PRIMEIRO campo da lista CAMPOS PENDENTES acima!\n"
                contexto += f"🚨 NÃO REPITA campos já preenchidos! Use apenas campos da lista PENDENTES!\n"
            else:
                contexto += "\n✅ TODOS OS CAMPOS PREENCHIDOS! Procure botão de submit para finalizar.\n"
        
        if acoes_repetidas > 0:
            contexto += f"\n⚠️ AVISO: {acoes_repetidas} das ultimas acoes foram repetidas. "
            contexto += "Considere tentar seletores diferentes ou acoes alternativas para progredir.\n"
    
    return contexto


def _construir_instrucoes_finais(instrucoes_custom: Optional[str], contexto: str) -> str:
    """Constroi instrucoes finais baseadas no contexto"""
    
    if instrucoes_custom:
        base_instruction = f"TAREFA ESPECÍFICA: {instrucoes_custom}\n\n"
        
        # Adicionar dicas especificas se for cadastro
        if "cadastro" in instrucoes_custom.lower() or "register" in instrucoes_custom.lower():
            # Verificar se já temos elementos de cadastro disponíveis
            # Se não temos campos customer.*, precisamos navegar primeiro
            base_instruction += """DICAS PARA CADASTRO:

[ALERTA] ANTES DE PREENCHER CAMPOS - VERIFIQUE:
Se você NÃO vê campos #customer.firstName na lista de elementos, significa que ainda não está na página de cadastro.

NAVEGACAO NECESSARIA:
1. PROCURE por link ou botão com texto: "Register", "Sign Up", "Cadastrar", "Registrar"
2. CLIQUE no link/botão para navegar para a página de cadastro
3. AGUARDE a página de cadastro carregar
4. SÓ ENTÃO preencha os campos na sequência

[ALERTA] SEQUENCIA LOGICA DE PREENCHIMENTO (apenas quando estiver na página de cadastro):
1. PRIMEIRO: USE "type" em [name='customer.firstName'] com valor "Joao Silva"
2. SEGUNDO: USE "type" em [name='customer.lastName'] com valor "Silva"  
3. TERCEIRO: USE "type" em [name='customer.address.street'] com valor "Rua das Flores, 123"
4. QUARTO: USE "type" em [name='customer.address.city'] com valor "Sao Paulo"
5. QUINTO: USE "type" em [name='customer.address.state'] com valor "SP"
6. SEXTO: USE "type" em [name='customer.address.zipCode'] com valor "01234-567"
7. SETIMO: USE "type" em [name='customer.phoneNumber'] com valor "11999999999"
8. OITAVO: USE "type" em [name='customer.ssn'] com valor "123456789"
9. NONO: USE "type" em [name='customer.username'] com valor "joao123"
10. DECIMO: USE "type" em [name='customer.password'] com valor "senha123"
11. FINAL: USE "click" no botão input[type='submit'][value='Register']

REGRAS CRITICAS:
- NAO tente preencher #customer.firstName se ele NAO estiver na lista de elementos disponíveis
- Se tentou preencher um campo e FALHOU, verifique se precisa navegar primeiro
- SEMPRE use apenas seletores da lista "ELEMENTOS DISPONIVEIS" EXATAMENTE como aparecem
- COPIE o seletor completo da lista (ex: input[type='submit'][value='Register'])
- NAO invente ou modifique seletores - use apenas os da lista
- Se viu ações repetidas falhando, mude de estratégia: procure navegação

DADOS FAKE PARA USAR (com acao "type"):
- [name='customer.firstName'] → "Joao Silva"
- [name='customer.lastName'] → "Silva" 
- [name='customer.address.street'] → "Rua das Flores, 123"
- [name='customer.address.city'] → "Sao Paulo"
- [name='customer.address.state'] → "SP"  
- [name='customer.address.zipCode'] → "01234-567"
- [name='customer.phoneNumber'] → "11999999999"
- [name='customer.ssn'] → "123456789"
- [name='customer.username'] → "joao123"
- [name='customer.password'] → "senha123"

"""
        
        return base_instruction + "Analise os elementos disponiveis, veja quais ja foram preenchidos, e escolha o PRÓXIMO campo da sequencia para completar."
    
    # Instrucoes baseadas no contexto
    if "login" in contexto.lower():
        return "Identifique campos de login (email/usuario e senha) e botao de submit. Priorize preencher dados de acesso com dados fake."
    elif "formulario" in contexto.lower() or "register" in contexto.lower():
        return "Identifique campos obrigatorios do formulario e botao de envio. Complete os dados necessarios com informacoes fake apropriadas seguindo a ordem logica."
    else:
        return "Analise a pagina e identifique a proxima acao mais logica para navegar ou interagir com o conteudo."


def _modelo_suporta_imagem(modelo: str) -> bool:
    """Verifica se o modelo suporta imagens"""
    modelos_com_visao = ["qwen2.5-vl", "llava", "gpt-4-vision", "gemini-pro-vision", "claude-3"]
    return any(visao in modelo.lower() for visao in modelos_com_visao)


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
        print(f"⚠️ Erro ao analisar HTML basico: {e}")
        html_relevante = html[:6000]
        elementos_encontrados = ["ERRO: Nao foi possivel analisar elementos"]
    
    # Detectar se ha campos de formulario nos seletores validos
    tem_campos_form = any(('#customer.' in sel or 'firstName' in sel or 'lastName' in sel) for sel in seletores_validos)
    
    # Identificar campos ja preenchidos do historico
    campos_preenchidos = set()
    if historico_acoes:
        # Identificar campos preenchidos do historico
        for acao in historico_acoes:
            # Compatibilidade com ambos os formatos (acao/action)
            acao_tipo = acao.get('acao') or acao.get('action')
            if (acao_tipo == 'type' and 
                acao.get('sucesso', False) and 
                (acao.get('seletor') or acao.get('selector'))):
                seletor = acao.get('seletor') or acao.get('selector')
                campos_preenchidos.add(seletor)
    
    if tem_campos_form:
        campos_form = [sel for sel in seletores_validos if '#customer.' in sel or 'firstName' in sel or 'lastName' in sel]
    
    # Marcar elementos ja preenchidos na lista
    elementos_marcados = []
    for elemento in elementos_encontrados:
        marcado = elemento
        # Verificar se algum seletor preenchido esta no elemento
        for campo in campos_preenchidos:
            if campo in elemento:
                marcado += " [OK] JÁ PREENCHIDO"
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

HISTÓRICO DE PROGRESSO:"""
    
    # Adicionar informacoes sobre campos preenchidos
    if campos_preenchidos:
        prompt += f"""
[OK] CAMPOS JÁ PREENCHIDOS ({len(campos_preenchidos)}):"""
        for campo in sorted(campos_preenchidos):
            prompt += f"""
   • {campo}"""
        prompt += f"""

[ALERTA] ATENÇÃO CRÍTICA: NÃO REPITA campos ja preenchidos!
[FOCO] PRÓXIMA AÇÃO OBRIGATÓRIA: Escolha o PRÓXIMO campo vazio da sequencia!
[PROIBIDO] PROIBIDO: Usar seletores ja preenchidos acima!

[FOCO] SEQUÊNCIA OBRIGATÓRIA DE PREENCHIMENTO:"""
    
    # Adicionar sequencia de campos com status dinâmico
    campos_sequencia = [
        "#customer.firstName",
        "#customer.lastName", 
        "#customer.address.street",
        "#customer.address.city",
        "#customer.address.state"
    ]
    
    for i, campo in enumerate(campos_sequencia, 1):
        status = "[OK] JÁ FEITO" if campo in campos_preenchidos else "[ACAO] FAZER AGORA"
        prompt += f"\n{i}. {campo} <- {status}"
    
    prompt += ""

    # Adicionar aviso especifico se ha campos de formulario
    if tem_campos_form:
        prompt += """
ATENCAO: CAMPOS DE FORMULARIO DETECTADOS!
- Vejo campos #customer.firstName, #customer.lastName, etc. na lista
- Use acao type para PREENCHER estes campos com dados fake
- NAO continue clicando em links, PREENCHA os campos visiveis!
- Siga a SEQUENCIA LOGICA: firstName -> lastName -> street -> city -> state -> zipCode -> phoneNumber -> ssn -> username -> password
- Exemplo: {"acao": "type", "seletor": "#customer.firstName", "valor": "Joao Silva"}

SEQUENCIA DE PREENCHIMENTO:
1. #customer.firstName - Nome
2. #customer.lastName - Sobrenome  
3. #customer.address.street - Endereco
4. #customer.address.city - Cidade
5. #customer.address.state - Estado
6. #customer.address.zipCode - CEP
7. #customer.phoneNumber - Telefone
8. #customer.ssn - SSN/CPF
9. #customer.username - Nome de usuario
10. #customer.password - Senha
"""
    
    prompt += """
REGRAS DE ACOES:
- "click": Para clicar em links, botoes, checkboxes
- "type": Para PREENCHER campos de texto (input, textarea) - USE SEMPRE PARA CAMPOS DE INPUT!
- "submit": APENAS para enviar formularios completos (botoes submit)
- "scroll": Para rolar a pagina
- "wait": Para aguardar carregamento

DADOS FAKE PARA FORMULARIOS:
- Nome: Use "Joao Silva" ou "Maria Santos"
- Email: Use "joao@email.com" ou "teste@email.com"  
- Senha: Use "123456" ou "senha123"
- Telefone: Use "11999999999" ou "(11) 99999-9999"
- CPF: Use "12345678901"
- Endereco: Use "Rua das Flores, 123"
- Cidade: Use "Sao Paulo"
- CEP: Use "01234-567"

IMPORTANTE: 
- Use APENAS seletores dos ELEMENTOS ENCONTRADOS acima
- COPIE o seletor EXATAMENTE como aparece na lista (incluindo colchetes, aspas e formato completo)
- EXEMPLO CORRETO: input[type='submit'][value='Register'] (não [name='Register'])
- Para PREENCHER campos INPUT use sempre acao "type" com valor
- Para ENVIAR formulario use "submit" em botao de envio
- Responda APENAS com JSON valido, sem markdown ou explicacoes extras
- Para login: procure campos de CPF/email e senha"""
    
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024
    }
    
    return payload, seletores_validos[:20]  # Limitar seletores


def gerar_instrucoes_contextuais(elementos: List[Dict], contexto: str) -> str:
    """Gera instrucoes contextuais baseadas nos elementos encontrados"""
    
    if not elementos:
        return "Nao foram encontrados elementos interativos na pagina."
    
    # Analisar tipos de elementos
    tipos_elementos = {}
    for el in elementos:
        tag = el.get('tag', 'unknown')
        tipos_elementos[tag] = tipos_elementos.get(tag, 0) + 1
    
    instrucoes = f"Encontrados {len(elementos)} elementos interativos:\n"
    for tag, count in tipos_elementos.items():
        instrucoes += f"- {count} {tag}(s)\n"
    
    # Sugestoes baseadas no contexto
    if contexto == "login":
        instrucoes += "\nSugestao: Procure por campos 'email', 'password' e botao 'submit'"
    elif contexto == "formulario":
        instrucoes += "\nSugestao: Complete campos obrigatorios (*) antes de submeter"
    elif contexto == "navegacao":
        instrucoes += "\nSugestao: Procure por links ou botoes de navegacao"
    
    return instrucoes


def otimizar_payload_para_modelo(payload: Dict, modelo: str) -> Dict:
    """Otimiza payload especifico para cada modelo"""
    
    # Configuracoes especificas por modelo
    if "qwen" in modelo.lower():
        payload["temperature"] = 0.1
        payload["top_p"] = 0.9
    elif "gemma" in modelo.lower():
        payload["temperature"] = 0
        payload["top_k"] = 40
    elif "llama" in modelo.lower():
        payload["temperature"] = 0.2
        payload["repeat_penalty"] = 1.1
    
    return payload


def extrair_elementos_otimizados_llm(pagina):
    """Extrai elementos otimizados da pagina para LLM"""
    try:
        from bs4 import BeautifulSoup
        from .html_parser import extrair_elementos_interativos_completos
        
        soup = BeautifulSoup(pagina.content(), 'html.parser')
        elementos = extrair_elementos_interativos_completos(soup, pagina)
        
        return {
            'elementos': elementos[:20],  # Limitar para nao sobrecarregar
            'html': str(soup)[:5000],     # HTML truncado
            'title': soup.find('title').get_text() if soup.find('title') else 'Sem titulo'
        }
    except Exception as e:
        logging.error(f"Erro ao extrair elementos: {e}")
        return {'elementos': [], 'html': '', 'title': 'Erro na extracao'}


def gerar_prompt_autonomo_completo(html_content, screenshot_path=None, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b", historico_acoes=None, pagina=None):
    """Gera prompt autonomo completo - wrapper para compatibilidade"""
    return gerar_prompt_em_chat_format(
        html=html_content,
        screenshot_path=screenshot_path,
        instrucoes_customizadas=instrucoes_customizadas,
        modelo=modelo,
        historico_acoes=historico_acoes
    )


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
        
        # Tentar validar resposta
        if validar_resposta_llm(resposta_limpa):
            acao_data = json.loads(resposta_limpa)
            seletor = acao_data.get('seletor')
            
            # Usar validacao flexivel em vez de verificacao simples
            valido, motivo = validar_seletor_existente(seletor, seletores_validos)
            
            if valido:
                print(f"[OK] Seletor '{seletor}' valido! ({motivo})")
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
            if validar_resposta_llm(resposta_retry_limpa):
                acao_retry = json.loads(resposta_retry_limpa)
                seletor_retry = acao_retry.get('seletor')
                valido_retry, motivo_retry = validar_seletor_existente(seletor_retry, seletores_validos)
                if valido_retry:
                    return acao_retry
                    
        else:
            print(f"[ERRO] [VALIDAÇÃO] Resposta nao passou na validacao basica")
                
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
