import json
import re
import os
import base64
from bs4 import BeautifulSoup

# Histórico de seletores já clicados durante a sessão
seletores_clicados = set()

# Estado dos campos preenchidos para evitar repetição
campos_preenchidos = set()

# Mapeamento de ações repetidas para debounce
acoes_repetidas = {}

def limpar_estado_campos():
    """Limpa o estado dos campos preenchidos (usar ao mudar de página/formulário)"""
    global campos_preenchidos
    campos_preenchidos.clear()

def adicionar_campo_preenchido(seletor):
    """Adiciona um campo à lista de preenchidos"""
    global campos_preenchidos
    campos_preenchidos.add(seletor)

def campo_ja_preenchido(seletor):
    """Verifica se um campo já foi preenchido"""
    global campos_preenchidos
    return seletor in campos_preenchidos

# ===================== Apoio: Extração e Prompt (padrão) =====================

def extrair_html(pagina):
    return pagina.content()


def escapar_css_id(id_value):
    """Escapa caracteres especiais em IDs para seletores CSS"""
    if not id_value:
        return ""
    # Escapar pontos e outros caracteres especiais
    escaped = id_value.replace('.', '\\.')
    escaped = escaped.replace(':', '\\:')
    escaped = escaped.replace('[', '\\[')
    escaped = escaped.replace(']', '\\]')
    return escaped

def gerar_selector(el):
    # 1. Prioridade máxima: ID (com escape correto)
    if el.has_attr("id"):
        id_escaped = escapar_css_id(el["id"])
        return f'#{id_escaped}'
    
    # 2. Data-testid (muito específico)
    if el.has_attr("data-testid"):
        return f'[data-testid="{el["data-testid"]}"]'
    
    # 3. Name para inputs (único e estável)
    if el.name == "input" and el.has_attr("name"):
        return f'input[name="{el["name"]}"]'
    
    # 4. Type específico para inputs
    if el.name == "input" and el.has_attr("type"):
        input_type = el["type"]
        if input_type in ["submit", "button"]:
            if el.has_attr("value"):
                return f'input[type="{input_type}"][value="{el["value"]}"]'
            else:
                return f'input[type="{input_type}"]'
        return f'input[type="{input_type}"]'
    
    # 5. Classes CSS (específicas)
    if el.has_attr("class"):
        classes = ".".join(el["class"]) 
        return f'.{classes}'
    
    # 6. Nome + atributos específicos
    if el.has_attr("name"):
        return f'{el.name}[name="{el["name"]}"]'
        
    # 7. Texto único (para botões/links)
    texto = (el.text or "").strip()
    if texto and len(texto) > 2 and len(texto) < 50:
        return f'{el.name}:contains("{texto}")'
    
    # 8. Fallback por tag
    return el.name


def gerar_prompt_em_chat_format(html, screenshot_path=None, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b", historico_acoes=None):
    soup = BeautifulSoup(html, "html.parser")
    elementos = []
    seletores_validos = []  # Lista para validação

    # ✅ EXPANSÃO: Capturar TODOS os elementos clicáveis possíveis
    tags_clicaveis = ["button", "a", "input", "div", "span", "i", "img", "li", "td", "th"]
    elementos_encontrados = soup.find_all(tags_clicaveis)
    
    for el in elementos_encontrados:
        texto = (el.text or el.get("value") or el.get("alt") or el.get("title") or "").strip()
        seletor = gerar_selector(el)
        tag = el.name

        # Pular elementos sem texto ou atributos úteis
        if not texto and not el.get("onclick") and not el.get("href") and not el.get("data-testid"):
            continue
            
        # Pular elementos muito genéricos sem contexto
        if len(texto) < 2 and not el.get("data-testid") and not el.get("href"):
            continue

        # Priorizar data-testid se existir
        testid = el.get("data-testid", "")
        if testid:
            seletor_preferido = f'[data-testid="{testid}"]'
        else:
            seletor_preferido = seletor

        # Extrair HREF especificamente
        href = el.get("href", "")
        
        # Extrair outros atributos úteis
        extras = []
        for attr in ["type", "aria-label", "placeholder", "title", "onclick", "role"]:
            if el.has_attr(attr):
                extras.append(f'{attr.upper()}: "{el[attr]}"')
        extras_str = " | ".join(extras) if extras else ""

        # ✅ SEMPRE incluir elementos válidos (LLM precisa ver TODOS)
        if seletor_preferido:
            descricao = f'[TEXTO: "{texto}", SELECTOR: "{seletor_preferido}", TAG: {tag}, HREF: "{href}"'
            if testid:
                descricao += f', TESTID: "{testid}"'
            if extras_str:
                descricao += f', {extras_str}'
            descricao += ']'
            elementos.append(descricao)
            seletores_validos.append(seletor_preferido)

    # ✅ OTIMIZAÇÃO: Priorizar elementos mais relevantes mas manter todos
    elementos_priorizados = []
    elementos_secundarios = []
    
    for i, elem in enumerate(elementos):
        # Alta prioridade: botões, links com href, inputs, elementos com data-testid
        if any(keyword in elem.lower() for keyword in [
            'button', 'data-testid=', 'href="/', 'input', 'submit', 'login', 'cadastr', 'entrar', 
            'acessar', 'registr', 'criar', 'novo', 'continuar', 'próximo', 'avançar'
        ]):
            elementos_priorizados.append(f"🔥 {elem}")
        else:
            elementos_secundarios.append(f"📋 {elem}")
    
    # Combinar priorizados + secundários (limitando secundários se muitos)
    if len(elementos_secundarios) > 30:
        elementos_secundarios = elementos_secundarios[:30] + [f"📋 ... ({len(elementos_secundarios) - 30} elementos adicionais ocultos)"]
    
    todos_elementos = elementos_priorizados + elementos_secundarios
    lista = "\n".join(todos_elementos) if todos_elementos else "Nenhum elemento interativo encontrado."

    # Preparar imagem se screenshot fornecido (somente se o modelo suportar visão)
    image_content = None
    modelo_lower = (modelo or "").lower()
    is_vision_model = any(term in modelo_lower for term in [
        "-vl", " vision", "llava", "minicpm-v", "qwen-vl", "gpt-4-vision", "idefics", "kosmos"
    ])
    if is_vision_model and screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}"
                }
            }

    # Determinar objetivo baseado nas instruções customizadas
    if instrucoes_customizadas and instrucoes_customizadas.strip():
        objetivo = f"OBJETIVO CUSTOMIZADO: {instrucoes_customizadas.strip()}"
    else:
        objetivo = "OBJETIVO: Navegar no site de concursos - escolha elementos que levem a informações sobre concursos, editais, inscrições, etc."

    # Construir seção de histórico se disponível
    historico_texto = ""
    if historico_acoes and len(historico_acoes) > 0:
        historico_texto = "\n\nHISTÓRICO DE AÇÕES ANTERIORES:\n"
        for i, ac in enumerate(historico_acoes, 1):
            status = "✅ NAVEGOU" if ac.get('navegacao') else "⚡ MESMA PÁGINA"
            msg_res = f" | resultado: {ac.get('resultado', {}).get('message','')}" if ac.get('resultado') else ""
            historico_texto += f"{i}. [{ac.get('timestamp','')}] {ac.get('acao','')} → {status}{msg_res}\n"
            if ac.get('navegacao'):
                historico_texto += f"   URL: {ac.get('url_antes','')} → {ac.get('url_depois','')}\n"
        
        # Usar o conjunto global de campos preenchidos
        if campos_preenchidos:
            historico_texto += f"\n🔒 CAMPOS JÁ PREENCHIDOS COM SUCESSO: {', '.join(sorted(campos_preenchidos))}\n"
        
        historico_texto += "\n⚠️  IMPORTANTE: NÃO REPITA ações em campos já preenchidos com sucesso!\nCONSIDERE o progresso acima ao escolher a próxima ação.\n"

    # Texto condicional baseado se há imagem ou não
    if image_content:
        prompt_inicio = "Você é um agente de QA automatizado. Analise a imagem da página e a lista de elementos para escolher o mais relevante."
        instrucao_visual = "3. Olhe a imagem fornecida para ver os elementos visuais da página"
        final_prompt = "Baseado na imagem e no histórico, escolha o elemento mais apropriado para continuar o objetivo:"
    else:
        prompt_inicio = "Você é um agente de QA automatizado. Analise a lista de elementos para escolher o mais relevante."
        instrucao_visual = "3. Analise os elementos textuais disponíveis listados abaixo"
        final_prompt = "Baseado na lista de elementos e no histórico, escolha o elemento mais apropriado para continuar o objetivo:"

    prompt_usuario = f"""
{prompt_inicio}

INSTRUÇÕES:
1. 🎯 EXECUTE **UMA ÚNICA AÇÃO** por resposta
2. 📋 ESCOLHA **APENAS** um seletor da lista abaixo (não invente seletores)
{instrucao_visual}
4. Responda APENAS com um JSON VÁLIDO na PRIMEIRA linha, sem markdown, sem ``` e sem explicações
5. Use o SELECTOR EXATO da lista (não modifique)
6. A resposta deve conter SOMENTE as chaves action e selector

🚨 CRÍTICO: **ESCOLHA APENAS** entre os seletores listados abaixo!
🚨 Se o seletor não estiver na lista, NÃO use - escolha outro da lista!

{objetivo}{historico_texto}

FORMATO OBRIGATÓRIO (copie exatamente):
{{"action": "click", "selector": "SELETOR_EXATO_DA_LISTA"}}

ELEMENTOS DISPONÍVEIS:
{lista}

{final_prompt}"""

    # Construir mensagens: multimodal apenas para modelos de visão, senão apenas texto
    if image_content:
        messages = [
            {
                "role": "user",
                "content": [image_content, {"type": "text", "text": prompt_usuario}]
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": prompt_usuario
            }
        ]
    
    # Definir max_tokens de forma segura (evitar 400 por contexto excedido)
    safe_max_tokens = 2048
    payload = {
        "model": modelo,
        "messages": messages,
        "temperature": 0,
        "top_p": 1,
        "max_tokens": safe_max_tokens,
        "stop": ["\n\n", "\r\n\r\n"]
    }
    
    return payload, seletores_validos


def validar_seletor_e_retry(resposta_llm, seletores_validos, chamar_llm_func, payload_original, max_tentativas=3):
    """
    Valida se o seletor retornado está na lista válida.
    Se não estiver, faz retry com mensagem de erro.
    """
    for tentativa in range(max_tentativas):
        acao = extrair_json_da_resposta(resposta_llm)
        
        if not acao:
            print(f"[ERRO] Tentativa {tentativa + 1}: JSON inválido na resposta")
            if tentativa < max_tentativas - 1:
                # Retry com mensagem de erro
                payload_retry = json.loads(json.dumps(payload_original))
                erro_msg = """🚨 ERRO CRÍTICO: Formato inválido!

VOCÊ DEVE responder com UM JSON VÁLIDO na PRIMEIRA linha, exemplo:
{"action": "click", "selector": "#customer\\.firstName"}

NÃO use:
- Markdown (```json)
- Explicações
- Múltiplas linhas
- Texto adicional

RESPONDA AGORA APENAS com o JSON:"""
                
                if isinstance(payload_retry["messages"][-1]["content"], list):
                    payload_retry["messages"][-1]["content"][0]["text"] += f"\n\n{erro_msg}"
                else:
                    payload_retry["messages"][-1]["content"] += f"\n\n{erro_msg}"
                
                resposta_llm = chamar_llm_func(payload_retry)
                continue
            else:
                return None
        
        seletor = acao.get("selector", "")
        
        # Usar normalização para validação
        if seletor_esta_na_lista(seletor, seletores_validos):
            print(f"[✅] Seletor válido encontrado: {seletor}")
            return acao
        else:
            print(f"[⚠️] Tentativa {tentativa + 1}: Seletor inválido '{seletor}' não está na lista")
            print(f"[DEBUG] Seletor normalizado: '{normalizar_seletor(seletor)}'")
            print(f"[DEBUG] Primeiros 5 seletores válidos: {seletores_validos[:5]}")
            if tentativa < max_tentativas - 1:
                payload_retry = json.loads(json.dumps(payload_original))
                erro_msg = f"""🚨 ERRO: Seletor inválido!

O seletor '{seletor}' NÃO EXISTE na lista fornecida.

VOCÊ DEVE:
1. Escolher APENAS um dos seletores listados abaixo
2. Copiar o seletor EXATAMENTE como está
3. Responder com JSON válido em uma linha

SELETORES DISPONÍVEIS: {', '.join(seletores_validos[:10])}

RESPONDA AGORA com JSON usando UM destes seletores:"""
                
                if isinstance(payload_retry["messages"][-1]["content"], list):
                    payload_retry["messages"][-1]["content"][0]["text"] += f"\n\n{erro_msg}"
                else:
                    payload_retry["messages"][-1]["content"] += f"\n\n{erro_msg}"
                
                resposta_llm = chamar_llm_func(payload_retry)
                continue
    
    print(f"[❌] Falha após {max_tentativas} tentativas. Nenhum seletor válido encontrado.")
    return None


def sanitizar_e_parsear_json(resposta_bruta):
    """
    Sanitiza e parseia resposta do LLM à prova de formatação inconsistente
    Remove ```json, normaliza aspas, etc.
    """
    if not resposta_bruta or not resposta_bruta.strip():
        print("[ERRO] Resposta vazia do LLM")
        return None
    
    # Log da resposta original para debug
    print(f"[DEBUG] Resposta original do LLM: {repr(resposta_bruta[:100])}...")
    
    # Detectar uso incorreto de markdown
    if '```' in resposta_bruta:
        print("⚠️ [AVISO] LLM usou markdown (```), será removido automaticamente")
    
    # Remover cercas de código e prefixos
    texto = resposta_bruta.strip()
    texto = re.sub(r'^```[\s\S]*?\n', '', texto)  # Remove ```json\n
    texto = re.sub(r'```$', '', texto)  # Remove ``` do final
    texto = texto.strip()
    
    # Tentar parse normal primeiro
    try:
        resultado = json.loads(texto)
        print("✅ [SUCESSO] JSON parseado corretamente")
        return resultado
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ [ERRO] Parse JSON falhou: {e}")
    
    # Tentar corrigir aspas simples → duplas
    try:
        texto_corrigido = texto.replace("'", '"')
        resultado = json.loads(texto_corrigido)
        print("✅ [SUCESSO] JSON corrigido (aspas simples → duplas)")
        return resultado
    except (json.JSONDecodeError, ValueError):
        print("❌ [ERRO] Correção de aspas falhou")
    
    # Última tentativa: extrair JSON válido da resposta
    try:
        # Procurar padrão {"action":...,"selector":...}
        match = re.search(r'\{[^{}]*"action"[^{}]*"selector"[^{}]*\}', texto)
        if match:
            json_candidato = match.group(0)
            json_candidato = json_candidato.replace("'", '"')
            resultado = json.loads(json_candidato)
            print("✅ [SUCESSO] JSON extraído via regex")
            return resultado
    except (json.JSONDecodeError, ValueError):
        print("❌ [ERRO] Extração por regex falhou")
    
    print(f"[ERRO] Não foi possível parsear JSON: {resposta_bruta[:200]}...")
    return None

def normalizar_seletor(seletor):
    """
    Normaliza seletores CSS para comparação consistente
    """
    if not seletor:
        return ""
    
    s = seletor.strip()
    
    # Normalizar aspas em atributos: [data-testid='x'] -> [data-testid="x"]
    s = re.sub(r'\[\s*([^\]=\s]+)\s*=\s*\'([^\']+)\'\s*\]', r'[\1="\2"]', s)
    
    # Normalizar múltiplos espaços
    s = re.sub(r'\s+', ' ', s)
    
    # Remover espaços desnecessários dentro dos colchetes
    s = re.sub(r'\[\s+', '[', s)
    s = re.sub(r'\s+\]', ']', s)
    
    return s

def seletor_esta_na_lista(seletor, lista_permitida):
    """
    Verifica se seletor está na lista usando normalização
    """
    seletor_norm = normalizar_seletor(seletor)
    lista_normalizada = {normalizar_seletor(s) for s in lista_permitida}
    
    if seletor_norm in lista_normalizada:
        return True
    
    # Fallback especial para data-testid
    match = re.match(r'^\[data-testid="(.+)"\]$', seletor_norm)
    if match:
        valor = match.group(1)
        return any(normalizar_seletor(s) == f'[data-testid="{valor}"]' for s in lista_permitida)
    
    return False

def extrair_json_da_resposta(resposta_llm):
    """Extrai JSON da resposta do LLM usando sanitização robusta"""
    return sanitizar_e_parsear_json(resposta_llm)


# ===================== Execução de ações com verificação =====================

def executar_acao(pagina, resposta_llm):
    """Executa a ação solicitada pelo LLM e retorna um resultado estruturado.

    Retorno: dict(action, selector, value, success: bool, message: str)
    """
    acao = extrair_json_da_resposta(resposta_llm)
    if not acao:
        return {"action": None, "selector": None, "value": None, "success": False, "message": "JSON inválido"}

    seletor = acao.get("selector")
    action_type = acao.get("action")
    value = acao.get("value", "")  # Valor para ações de preenchimento

    result = {"action": action_type, "selector": seletor, "value": value, "success": False, "message": ""}

    # Verificar se já foi clicado (para cliques)
    if seletor in seletores_clicados and action_type == "click":
        result.update({"success": True, "message": "Clique ignorado (já clicado)"})
        return result
    
    # Verificar se campo já foi preenchido com sucesso (para preenchimento)
    if seletor in campos_preenchidos and action_type in ("fill", "type"):
        result.update({"success": True, "message": "Campo ignorado (já preenchido)"})
        return result

    try:
        if action_type == "click":
            el = pagina.locator(seletor).first

            try:
                seletor_escaped = seletor.replace('"', '\\"')
                pagina.evaluate(f"""
                    () => {{
                        const el = document.querySelector("{seletor_escaped}");
                        if (el) {{ el.scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }}
                    }}
                """)
                pagina.wait_for_timeout(300)
            except Exception:
                pass

            try:
                el.wait_for(state="visible", timeout=5000)
                el.click()
                seletores_clicados.add(seletor)
                result.update({"success": True, "message": "Clique OK"})
                return result
            except Exception:
                pass

            try:
                seletor_escaped = seletor.replace('"', '\\"')
                sucesso = pagina.evaluate(f"""
                    () => {{
                        const el = document.querySelector("{seletor_escaped}");
                        if (el) {{ el.click(); return true; }}
                        return false;
                    }}
                """)
            except Exception:
                sucesso = False

            if sucesso:
                seletores_clicados.add(seletor)
                result.update({"success": True, "message": "Clique OK (JS)"})
            else:
                result.update({"success": False, "message": "Clique FALHA"})
            return result

        elif action_type in ("fill", "type"):
            el = pagina.locator(seletor).first
            try:
                el.wait_for(state="visible", timeout=5000)
                try:
                    el.click(timeout=1000)
                except Exception:
                    pass
                el.clear()
                el.fill(value)
            except Exception as e:
                pass

            pagina.wait_for_timeout(150)
            try:
                current = el.input_value()
            except Exception:
                current = ""

            def norm_digits(s: str) -> str:
                return "".join(ch for ch in (s or "") if ch.isdigit())

            same_exact = (current == value)
            same_digits = (norm_digits(current) == norm_digits(value) and len(norm_digits(value)) >= 5)
            if same_exact or same_digits:
                campos_preenchidos.add(seletor)  # ✅ Marcar como preenchido com sucesso
                result.update({"success": True, "message": "Fill OK"})
                return result

            try:
                el.clear()
                el.type(value, delay=50)
            except Exception:
                pass
            pagina.wait_for_timeout(150)
            try:
                current2 = el.input_value()
            except Exception:
                current2 = ""
            same_exact2 = (current2 == value)
            same_digits2 = (norm_digits(current2) == norm_digits(value) and len(norm_digits(value)) >= 5)
            if same_exact2 or same_digits2:
                campos_preenchidos.add(seletor)  # ✅ Marcar como preenchido com sucesso
                result.update({"success": True, "message": "Fill OK (fallback)"})
                return result

            try:
                seletor_escaped = seletor.replace('"', '\\"')
                value_escaped = value.replace('"', '\\"')
                pagina.evaluate(f"""
                    () => {{
                        const el = document.querySelector("{seletor_escaped}");
                        if (el) {{
                            el.value = "{value_escaped}";
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}
                """)
                pagina.wait_for_timeout(100)
                current3 = el.input_value()
            except Exception:
                current3 = ""

            same_exact3 = (current3 == value)
            same_digits3 = (norm_digits(current3) == norm_digits(value) and len(norm_digits(value)) >= 5)
            if same_exact3 or same_digits3:
                campos_preenchidos.add(seletor)  # ✅ Marcar como preenchido com sucesso
                result.update({"success": True, "message": "Fill OK (JS)"})
            else:
                result.update({"success": False, "message": "Fill FALHA"})
            return result

        elif action_type == "submit":
            try:
                el = pagina.locator(seletor).first
                el.wait_for(state="visible", timeout=5000)
                try:
                    el.click()
                    result.update({"success": True, "message": "Submit OK"})
                    return result
                except Exception:
                    pass

                seletor_escaped = seletor.replace('"', '\\"')
                sucesso = pagina.evaluate(f"""
                    () => {{
                        const el = document.querySelector("{seletor_escaped}");
                        if (!el) return false;
                        if (el.tagName === 'FORM') {{ el.requestSubmit(); return true; }}
                        try {{ el.click(); return true; }} catch (e) {{ return false; }}
                    }}
                """)
                if sucesso:
                    result.update({"success": True, "message": "Submit OK (JS)"})
                else:
                    result.update({"success": False, "message": "Submit FALHA"})
            except Exception as e:
                result.update({"success": False, "message": f"Submit erro: {e}"})
            return result

        elif action_type == "press":
            key = value or "Enter"
            try:
                el = pagina.locator(seletor).first
                el.wait_for(state="visible", timeout=5000)
                el.press(key)
                result.update({"success": True, "message": f"Press '{key}' OK"})
            except Exception as e:
                result.update({"success": False, "message": f"Press '{key}' FALHA"})
            return result

        else:
            result.update({"success": False, "message": f"Ação desconhecida: {action_type}"})
            return result

    except Exception as e:
        result.update({"success": False, "message": f"Erro geral: {e}"})
        return result


def verificar_campo_preenchido(pagina, seletor):
    """
    Verifica se um campo realmente tem valor (não é placeholder).
    
    Returns:
        - True: Campo tem valor real
        - False: Campo vazio ou apenas placeholder
    """
    try:
        seletor_escaped = seletor.replace('"', '\\"')
        resultado = pagina.evaluate(f"""
            () => {{
                const el = document.querySelector("{seletor_escaped}");
                if (!el) return {{ status: 'not_found' }};
                
                const value = el.value || '';
                const placeholder = el.placeholder || '';
                
                // Verificar se tem valor real
                if (value && value.trim() !== '') {{
                    // Se valor é diferente do placeholder, é real
                    if (value !== placeholder) {{
                        return {{ status: 'filled', value: value, placeholder: placeholder }};
                    }}
                    // Se valor é igual ao placeholder, pode ser fake
                    return {{ status: 'maybe_placeholder', value: value, placeholder: placeholder }};
                }}
                
                // Campo vazio
                return {{ status: 'empty', value: value, placeholder: placeholder }};
            }}
        """)
        
        if resultado['status'] == 'filled':
            return True
        elif resultado['status'] == 'maybe_placeholder':
            # Para casos duvidosos, considerar como não preenchido
            return False
        else:
            return False
            
    except Exception as e:
        # Em caso de erro, assumir que não está preenchido
        return False


# ===================== UX: Cookies e Capturas =====================

def fechar_aviso_de_cookies(pagina):
    possiveis_botoes = [
        "text=Aceito", "text=Aceitar", "text=OK", "text=Entendi", "text=Concordo"
    ]
    for seletor in possiveis_botoes:
        try:
            pagina.locator(seletor).first.click(timeout=1000)
            return
        except Exception:
            continue


def salvar_lista_seletores(elementos, passo):
    os.makedirs("logs", exist_ok=True)
    caminho = f"logs/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(elementos))


def salvar_screenshot(pagina, passo):
    os.makedirs("prints", exist_ok=True)
    caminho = f"prints/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)


def extrair_elementos_interativos_completos(soup, page):
    """
    Extrai TODOS os elementos interativos da página de forma genérica
    Inclui: inputs, selects, textareas, buttons, submits, links
    Com contexto completo para o LLM decidir autonomamente
    """
    elementos = []
    
    print(f"🔍 [DEBUG] Iniciando extração completa...")
    
    # 1. INPUTS, SELECTS, TEXTAREAS (campos de formulário)
    campos_formulario = soup.find_all(['input', 'select', 'textarea'])
    print(f"🔍 [DEBUG] Encontrados {len(campos_formulario)} campos de formulário")
    
    for i, campo in enumerate(campos_formulario):
        print(f"🔍 [DEBUG] Campo {i+1}: {campo.name} type={campo.get('type')} id={campo.get('id')} name={campo.get('name')}")
        
        # Verificar se é visível e habilitado
        if not _elemento_visivel_e_habilitado(campo, page):
            print(f"🔍 [DEBUG] Campo {i+1} não visível/habilitado, pulando")
            continue
            
        # Extrair informações do campo
        info_campo = _extrair_info_campo(campo, soup)
        if info_campo:
            print(f"🔍 [DEBUG] Campo {i+1} adicionado: {info_campo['selector']}")
            elementos.append(info_campo)
        else:
            print(f"🔍 [DEBUG] Campo {i+1} falhou na extração de info")
    
    print(f"🔍 [DEBUG] Total campos válidos: {len([e for e in elementos if e.get('tag') in ['input', 'select', 'textarea']])}")
    
    # 2. BUTTONS E SUBMITS (botões de ação)
    botoes = soup.find_all(['button', 'input'])
    botoes_validos = 0
    for botao in botoes:
        if botao.name == 'input' and botao.get('type') not in ['submit', 'button', 'reset']:
            continue
            
        if not _elemento_visivel_e_habilitado(botao, page):
            continue
            
        info_botao = _extrair_info_botao(botao)
        if info_botao:
            elementos.append(info_botao)
            botoes_validos += 1
    
    print(f"🔍 [DEBUG] Total botões válidos: {botoes_validos}")
    
    # 3. LINKS (elementos <a>)
    links = soup.find_all('a', href=True)
    links_validos = 0
    for link in links:
        if not _elemento_visivel_e_habilitado(link, page):
            continue
            
        info_link = _extrair_info_link(link)
        if info_link:
            elementos.append(info_link)
            links_validos += 1
    
    print(f"🔍 [DEBUG] Total links válidos: {links_validos}")
    
    # 4. ELEMENTOS COM ROLE="button"
    role_buttons = soup.find_all(attrs={"role": "button"})
    role_validos = 0
    for elem in role_buttons:
        if not _elemento_visivel_e_habilitado(elem, page):
            continue
            
        info_role = _extrair_info_role_button(elem)
        if info_role:
            elementos.append(info_role)
            role_validos += 1
    
    print(f"🔍 [DEBUG] Total role buttons válidos: {role_validos}")
    
    # 5. DETECTAR CONTEXTO DA PÁGINA
    contexto_pagina = _detectar_contexto_pagina(soup, elementos)
    print(f"🔍 [DEBUG] Contexto detectado: {contexto_pagina}")
    
    # 6. RANKEAR E PRIORIZAR ELEMENTOS
    elementos_priorizados = _priorizar_elementos(elementos, contexto_pagina)
    
    print(f"🔍 [DEBUG] Total elementos finais: {len(elementos_priorizados)}")
    
    return elementos_priorizados[:80], contexto_pagina  # Limitar a 80 elementos

def _elemento_visivel_e_habilitado(elemento, page):
    """Verifica se elemento está visível e habilitado usando Playwright"""
    try:
        # Gerar seletor único para verificar visibilidade
        seletor = gerar_selector(elemento)
        if not seletor:
            return False
            
        # Verificar via Playwright se está visível e habilitado
        locator = page.locator(seletor).first
        return locator.is_visible() and locator.is_enabled()
    except Exception:
        # Fallback: verificar atributos básicos
        return not (elemento.get('disabled') or elemento.get('hidden') or 
                   elemento.get('style', '').find('display:none') >= 0 or
                   elemento.get('style', '').find('visibility:hidden') >= 0)

def _extrair_info_campo(campo, soup):
    """Extrai informações completas de um campo de formulário"""
    tag = campo.name
    tipo = campo.get('type', '')
    
    # Pular tipos não interativos
    if tipo in ['hidden', 'submit', 'button', 'reset']:
        return None
    
    # Gerar seletor único
    seletor = gerar_selector(campo)
    if not seletor:
        return None
    
    # Escapar pontos no ID se necessário (ParaBank: customer.firstName)
    if campo.get('id') and '.' in campo.get('id'):
        id_original = campo.get('id')
        seletor = seletor.replace(f"#{id_original}", f"#{id_original.replace('.', '\\\\.')}")
    
    # Encontrar label associado
    label_text = _encontrar_label(campo, soup)
    
    info = {
        "selector": seletor,
        "tag": tag,
        "type": tipo or 'text',
        "name": campo.get('name', ''),
        "id": campo.get('id', ''),
        "labelText": label_text,
        "placeholder": campo.get('placeholder', ''),
        "required": campo.has_attr('required'),
        "maxlength": campo.get('maxlength', ''),
        "pattern": campo.get('pattern', ''),
        "aria_label": campo.get('aria-label', ''),
        "priority": "🔥"  # Alta prioridade para campos de formulário
    }
    
    # Adicionar opções para select
    if tag == 'select':
        opcoes = [opt.get_text(strip=True) for opt in campo.find_all('option') if opt.get_text(strip=True)]
        info["options"] = opcoes[:10]  # Limitar opções
    
    return info

def _extrair_info_botao(botao):
    """Extrai informações de botões"""
    seletor = gerar_selector(botao)
    if not seletor:
        return None
    
    # Texto do botão
    if botao.name == 'input':
        texto = botao.get('value', '')
    else:
        texto = botao.get_text(strip=True)
    
    if not texto:
        return None
    
    return {
        "selector": seletor,
        "tag": botao.name,
        "type": botao.get('type', ''),
        "text": texto,
        "aria_label": botao.get('aria-label', ''),
        "priority": "🔥" if _eh_botao_importante(texto) else "📋"
    }

def _extrair_info_link(link):
    """Extrai informações de links"""
    seletor = gerar_selector(link)
    if not seletor:
        return None
    
    texto = link.get_text(strip=True)
    href = link.get('href', '')
    
    if not texto or len(texto) > 100:  # Ignorar links muito longos
        return None
    
    return {
        "selector": seletor,
        "tag": "a",
        "text": texto,
        "href": href,
        "aria_label": link.get('aria-label', ''),
        "priority": "🔥" if _eh_link_importante(texto) else "📋"
    }

def _extrair_info_role_button(elemento):
    """Extrai informações de elementos com role=button"""
    seletor = gerar_selector(elemento)
    if not seletor:
        return None
    
    texto = elemento.get_text(strip=True)
    if not texto:
        return None
    
    return {
        "selector": seletor,
        "tag": elemento.name,
        "role": "button",
        "text": texto,
        "aria_label": elemento.get('aria-label', ''),
        "priority": "🔥" if _eh_botao_importante(texto) else "📋"
    }

def _encontrar_label(campo, soup):
    """Encontra o label associado ao campo"""
    # 1. Por atributo for
    campo_id = campo.get('id')
    if campo_id:
        label = soup.find('label', {'for': campo_id})
        if label:
            return label.get_text(strip=True)
    
    # 2. Por elemento pai label
    label_pai = campo.find_parent('label')
    if label_pai:
        return label_pai.get_text(strip=True)
    
    # 3. Por irmão anterior
    anterior = campo.find_previous_sibling('label')
    if anterior:
        return anterior.get_text(strip=True)
    
    # 4. Por proximidade (div pai com label)
    pai = campo.find_parent(['div', 'fieldset', 'form-group'])
    if pai:
        label_proximo = pai.find('label')
        if label_proximo:
            return label_proximo.get_text(strip=True)
    
    return ""

def _eh_botao_importante(texto):
    """Identifica botões importantes"""
    texto_lower = texto.lower()
    palavras_importantes = [
        'submit', 'register', 'login', 'sign in', 'sign up', 'cadastrar', 'entrar',
        'enviar', 'confirmar', 'continuar', 'próximo', 'salvar', 'criar',
        'inscrever', 'aplicar', 'search', 'buscar', 'pesquisar'
    ]
    return any(palavra in texto_lower for palavra in palavras_importantes)

def _eh_link_importante(texto):
    """Identifica links importantes"""
    texto_lower = texto.lower()
    palavras_importantes = [
        'register', 'cadastr', 'signup', 'sign up', 'create account',
        'nova conta', 'login', 'entrar', 'acesso'
    ]
    return any(palavra in texto_lower for palavra in palavras_importantes)

def _detectar_contexto_pagina(soup, elementos):
    """Detecta o contexto/intenção da página"""
    # Contar tipos de elementos
    inputs = len([e for e in elementos if e.get('tag') in ['input', 'select', 'textarea']])
    botoes_submit = len([e for e in elementos if e.get('type') == 'submit' or 
                        (e.get('text', '').lower() in ['submit', 'enviar', 'register', 'cadastrar'])])
    
    contexto = {
        "tipo": "navegacao",  # padrão
        "tem_formulario": inputs >= 3 and botoes_submit >= 1,
        "total_inputs": inputs,
        "total_botoes": botoes_submit,
        "sugestao": ""
    }
    
    if contexto["tem_formulario"]:
        contexto["tipo"] = "formulario"
        contexto["sugestao"] = "Esta página contém um formulário. Preencha os campos em ordem e depois envie."
    
    # Detectar páginas específicas por título/conteúdo
    title = soup.find('title')
    if title:
        title_text = title.get_text().lower()
        if 'register' in title_text or 'cadastr' in title_text:
            contexto["sugestao"] = "Página de cadastro detectada. Preencha todos os campos obrigatórios."
        elif 'login' in title_text or 'entrar' in title_text:
            contexto["sugestao"] = "Página de login detectada. Preencha usuário e senha."
    
    return contexto

def _priorizar_elementos(elementos, contexto):
    """Prioriza elementos baseado no contexto"""
    # Se é formulário, priorizar campos de input primeiro
    if contexto["tem_formulario"]:
        inputs = [e for e in elementos if e.get('tag') in ['input', 'select', 'textarea']]
        botoes = [e for e in elementos if e.get('tag') in ['button'] or e.get('type') in ['submit', 'button']]
        links = [e for e in elementos if e.get('tag') == 'a']
        outros = [e for e in elementos if e not in inputs and e not in botoes and e not in links]
        
        return inputs + botoes + links + outros
    
    # Senão, priorizar por importância
    alta_prioridade = [e for e in elementos if e.get('priority') == '🔥']
    baixa_prioridade = [e for e in elementos if e.get('priority') == '📋']
    
    return alta_prioridade + baixa_prioridade


# ===================== Extração otimizada + Prompt =====================

def extrair_elementos_otimizados_llm(pagina):
    from datetime import datetime
    
    try:
        html = pagina.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        navegacao_llm = {
            "pagina": {
                "url": pagina.url,
                "titulo": soup.find('title').get_text().strip() if soup.find('title') else "Sem título",
                "timestamp": datetime.now().isoformat()
            },
            "navegacao_principal": [],
            "secoes_principais": [],
            "concursos_ativos": [],
            "elementos_interativos": {
                "botoes_principais": [],
                "botoes_acesso_concursos": [],
                "links_importantes": []
            },
            "campos_formulario": {
                "inputs_texto": [],
                "inputs_senha": [],
                "selects": [],
                "textareas": [],
                "botoes_submit": []
            },
            "contexto_para_llm": {
                "objetivo_pagina": "Portal de concursos e avaliações",
                "acoes_possiveis": [],
                "principais_caminhos": {}
            }
        }
        
        nav_links = soup.find_all('a', class_=['nav-link', 'menu-item', 'navbar-nav'])
        for link in nav_links:
            texto = link.get_text(strip=True)
            href = link.get('href', '')
            if texto and href and len(texto) > 2:
                navegacao_llm["navegacao_principal"].append({
                    "texto": texto,
                    "seletor": gerar_selector(link),
                    "url": href,
                    "tipo": "menu"
                })
        
        # ✅ BOTÕES EXPANDIDO: Capturar TODOS os elementos clicáveis
        tags_clicaveis = ['button', 'a', 'div', 'span', 'i', 'input']
        classes_clicaveis = ['btn', 'button', 'link', 'clickable', 'action', 'submit', 'primary', 'secondary']
        
        # Buscar por classes
        botoes_principais = []
        for tag in tags_clicaveis:
            for classe in classes_clicaveis:
                botoes_encontrados = soup.find_all(tag, class_=lambda x: x and classe in str(x).lower())
                botoes_principais.extend(botoes_encontrados)
        
        # Buscar por texto específico (cadastro, registro, etc.)
        texto_busca = ['cadastr', 'registr', 'criar', 'novo', 'inscrição', 'inscrever', 'participar', 'acessar', 'entrar', 'login', 'contato']
        for termo in texto_busca:
            elementos_texto = soup.find_all(string=lambda text: text and termo in text.lower())
            for texto_elem in elementos_texto:
                parent = texto_elem.parent
                if parent and parent.name in tags_clicaveis:
                    botoes_principais.append(parent)
        
        # Remover duplicatas
        botoes_unicos = []
        selectors_vistos = set()
        for botao in botoes_principais:
            try:
                seletor = gerar_selector(botao)
                if seletor not in selectors_vistos:
                    selectors_vistos.add(seletor)
                    botoes_unicos.append(botao)
            except Exception:
                continue
        
        for botao in botoes_unicos:
            texto = botao.get_text(strip=True)
            href = botao.get('href', '') if botao.name == 'a' else ''
            classes = ' '.join(botao.get('class', []))
            
            if not texto and not href:
                continue
                
            texto_lower = texto.lower()
            funcao = "navegacao"
            if "login" in texto_lower or "entrar" in texto_lower:
                funcao = "login"
            elif "cadastr" in texto_lower or "registr" in texto_lower:
                funcao = "cadastro"
            elif "concurso" in texto_lower or "avaliac" in texto_lower:
                funcao = "listar_concursos"
            elif "contato" in texto_lower:
                funcao = "contato"
            elif "inscri" in texto_lower:
                funcao = "inscricao"
            
            elemento_botao = {
                "texto": texto or f"Elemento {botao.name}",
                "seletor": gerar_selector(botao),
                "url": href,
                "funcao": funcao,
                "tipo": "primario" if "primary" in classes else "secundario"
            }
            
            if "primary" in classes or "btn-primary" in classes or funcao in ["login", "cadastro"]:
                navegacao_llm["elementos_interativos"]["botoes_principais"].append(elemento_botao)
            else:
                navegacao_llm["elementos_interativos"]["botoes_acesso_concursos"].append(elemento_botao)
        
        titulos_principais = soup.find_all(['h1', 'h2', 'h3', 'h4'], class_=['titulo', 'title', 'card-title'])
        for titulo in titulos_principais:
            texto_titulo = titulo.get_text(strip=True)
            if len(texto_titulo) < 3:
                continue
            descricao = ""
            next_elem = titulo.find_next(['p', 'div'])
            if next_elem:
                desc_text = next_elem.get_text(strip=True)
                if len(desc_text) > 10:
                    descricao = desc_text[:200]
            acao = None
            next_button = titulo.find_next(['a', 'button'])
            if next_button and next_button.get_text(strip=True):
                acao = {
                    "texto": next_button.get_text(strip=True),
                    "seletor": gerar_selector(next_button),
                    "url": next_button.get('href', '') if next_button.name == 'a' else ''
                }
            secao = {
                "titulo": texto_titulo,
                "seletor": gerar_selector(titulo),
                "tipo": "titulo_principal" if titulo.name == 'h1' else "secao"
            }
            if descricao:
                secao["descricao"] = descricao
            if acao:
                secao["acao"] = acao
            navegacao_llm["secoes_principais"].append(secao)
        
        cards = soup.find_all(['div'], class_=['card', 'item', 'concurso', 'avaliacao'])
        for card in cards:
            titulo_card = card.find(['h5', 'h4', 'h3'], class_=['card-title', 'titulo', 'title'])
            if not titulo_card:
                continue
            nome_item = titulo_card.get_text(strip=True)
            if len(nome_item) < 3:
                continue
            categoria = ""
            badge = card.find(['span', 'h6'], class_=['badge', 'tag', 'categoria'])
            if badge:
                categoria = badge.get_text(strip=True)
            descricao = ""
            desc_elem = card.find(['p'], class_=['card-text', 'description', 'desc'])
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if len(desc_text) > 10:
                    descricao = desc_text[:150]
            acao = None
            botao_acesso = card.find(['a', 'button'])
            if botao_acesso and botao_acesso.get_text(strip=True):
                acao = {
                    "texto": botao_acesso.get_text(strip=True),
                    "seletor": gerar_selector(botao_acesso),
                    "url": botao_acesso.get('href', '') if botao_acesso.name == 'a' else ''
                }
            item_info = {
                "nome": nome_item,
                "seletor": gerar_selector(titulo_card),
                "categoria": categoria,
                "descricao": descricao
            }
            if acao:
                item_info["acao"] = acao
            navegacao_llm["concursos_ativos"].append(item_info)
        
        inputs_texto = soup.find_all('input', {'type': ['text', 'email', 'tel', 'number']})
        for input_elem in inputs_texto:
            nome = input_elem.get('name', '')
            placeholder = input_elem.get('placeholder', '')
            label_text = ""
            label_id = input_elem.get('id', '')
            if label_id:
                label = soup.find('label', {'for': label_id})
                if label:
                    label_text = label.get_text(strip=True)
            if not label_text:
                parent = input_elem.find_parent(['div', 'form-group', 'field'])
                if parent:
                    label = parent.find('label')
                    if label:
                        label_text = label.get_text(strip=True)
            nome_campo = label_text or placeholder or nome or "Campo de texto"
            if len(nome_campo) > 2:
                navegacao_llm["campos_formulario"]["inputs_texto"].append({
                    "nome": nome_campo,
                    "seletor": gerar_selector(input_elem),
                    "tipo": input_elem.get('type', 'text'),
                    "obrigatorio": input_elem.has_attr('required'),
                    "placeholder": placeholder
                })
        
        inputs_senha = soup.find_all('input', {'type': 'password'})
        for input_elem in inputs_senha:
            nome = input_elem.get('name', '')
            placeholder = input_elem.get('placeholder', '')
            label_text = ""
            label_id = input_elem.get('id', '')
            if label_id:
                label = soup.find('label', {'for': label_id})
                if label:
                    label_text = label.get_text(strip=True)
            if not label_text:
                parent = input_elem.find_parent(['div', 'form-group', 'field'])
                if parent:
                    label = parent.find('label')
                    if label:
                        label_text = label.get_text(strip=True)
            nome_campo = label_text or placeholder or nome or "Campo de senha"
            navegacao_llm["campos_formulario"]["inputs_senha"].append({
                "nome": nome_campo,
                "seletor": gerar_selector(input_elem),
                "obrigatorio": input_elem.has_attr('required'),
                "placeholder": placeholder
            })
        
        selects = soup.find_all('select')
        for select_elem in selects:
            nome = select_elem.get('name', '')
            label_text = ""
            label_id = select_elem.get('id', '')
            if label_id:
                label = soup.find('label', {'for': label_id})
                if label:
                    label_text = label.get_text(strip=True)
            if not label_text:
                parent = select_elem.find_parent(['div', 'form-group', 'field'])
                if parent:
                    label = parent.find('label')
                    if label:
                        label_text = label.get_text(strip=True)
            opcoes = select_elem.find_all('option')
            nome_campo = label_text or nome or "Seleção"
            if len(nome_campo) > 2:
                navegacao_llm["campos_formulario"]["selects"].append({
                    "nome": nome_campo,
                    "seletor": gerar_selector(select_elem),
                    "opcoes": len(opcoes),
                    "obrigatorio": select_elem.has_attr('required')
                })
        
        textareas = soup.find_all('textarea')
        for textarea_elem in textareas:
            nome = textarea_elem.get('name', '')
            placeholder = textarea_elem.get('placeholder', '')
            label_text = ""
            label_id = textarea_elem.get('id', '')
            if label_id:
                label = soup.find('label', {'for': label_id})
                if label:
                    label_text = label.get_text(strip=True)
            if not label_text:
                parent = textarea_elem.find_parent(['div', 'form-group', 'field'])
                if parent:
                    label = parent.find('label')
                    if label:
                        label_text = label.get_text(strip=True)
            nome_campo = label_text or placeholder or nome or "Área de texto"
            if len(nome_campo) > 2:
                navegacao_llm["campos_formulario"]["textareas"].append({
                    "nome": nome_campo,
                    "seletor": gerar_selector(textarea_elem),
                    "obrigatorio": textarea_elem.has_attr('required'),
                    "placeholder": placeholder
                })
        
        botoes_submit = []
        botoes_submit.extend(soup.find_all(['button', 'input'], {'type': ['submit', 'button']}))
        botoes_submit.extend(soup.find_all(attrs={'role': 'button'}))
        botoes_texto = soup.find_all(['button', 'div', 'a'], string=lambda text: text and any(
            keyword in text.lower() for keyword in ['entrar', 'login', 'enviar', 'submit', 'confirmar', 'acessar']
        ))
        botoes_submit.extend(botoes_texto)
        botoes_submit.extend(soup.find_all(class_=lambda x: x and any(
            cls in str(x).lower() for cls in ['submit', 'login', 'btn-primary', 'send', 'confirm']
        )))
        botoes_submit.extend(soup.find_all(attrs={'data-testid': lambda x: x and any(
            keyword in x.lower() for keyword in ['submit', 'login', 'entrar', 'send']
        )}))
        
        botoes_submit_unicos = []
        selectors_vistos = set()
        for botao in botoes_submit:
            try:
                seletor = gerar_selector(botao)
                if seletor not in selectors_vistos:
                    selectors_vistos.add(seletor)
                    botoes_submit_unicos.append(botao)
            except Exception:
                continue
        
        for botao in botoes_submit_unicos:
            if botao.name == 'input':
                texto = botao.get('value', '')
            else:
                texto = botao.get_text(strip=True)
            if not texto:
                texto = botao.get('aria-label', '') or botao.get('title', '') or botao.get('data-testid', '')
            if texto and len(texto.strip()) > 1:
                texto_lower = texto.lower()
                funcao = "enviar"
                if "login" in texto_lower or "entrar" in texto_lower:
                    funcao = "login"
                elif "buscar" in texto_lower or "pesquisar" in texto_lower:
                    funcao = "buscar"
                elif "enviar" in texto_lower or "submit" in texto_lower:
                    funcao = "enviar"
                elif "cancelar" in texto_lower or "voltar" in texto_lower:
                    funcao = "cancelar"
                elif "confirmar" in texto_lower or "confirm" in texto_lower:
                    funcao = "confirmar"
                navegacao_llm["campos_formulario"]["botoes_submit"].append({
                    "texto": texto.strip(),
                    "seletor": gerar_selector(botao),
                    "funcao": funcao,
                    "tipo": botao.get('type', 'button'),
                    "tag": botao.name
                })
        
        acoes_possiveis = []
        principais_caminhos = {}
        for botao in navegacao_llm["elementos_interativos"]["botoes_principais"]:
            if botao["funcao"] == "login":
                acoes_possiveis.append("Fazer login na área do candidato")
                principais_caminhos["candidato"] = botao["url"]
            elif botao["funcao"] == "listar_concursos":
                acoes_possiveis.append("Consultar concursos e avaliações disponíveis")
                principais_caminhos["concursos"] = botao["url"]
            elif botao["funcao"] == "contato":
                acoes_possiveis.append("Entrar em contato")
                principais_caminhos["contato"] = botao["url"]
            elif botao["funcao"] == "inscricao":
                acoes_possiveis.append("Realizar inscrição")
                principais_caminhos["inscricao"] = botao["url"]
        for item in navegacao_llm["concursos_ativos"]:
            if item.get("acao"):
                acoes_possiveis.append(f"Acessar {item['nome']}")
        navegacao_llm["contexto_para_llm"]["acoes_possiveis"] = acoes_possiveis
        navegacao_llm["contexto_para_llm"]["principais_caminhos"] = principais_caminhos
        
        return navegacao_llm
        
    except Exception:
        return None


def verificar_estado_campos_formulario(page, seletores_campos):
    """
    Verifica o estado atual de todos os campos do formulário.
    
    Args:
        page: Página do Playwright
        seletores_campos: Lista de seletores de campos input
        
    Returns:
        dict: Estado dos campos {seletor: {'preenchido': bool, 'valor': str, 'placeholder': str}}
    """
    estado_campos = {}
    
    for seletor in seletores_campos:
        try:
            # Verificar se é campo de input
            if not any(tag in seletor.lower() for tag in ['input', '#', '[name=', '[id=']):
                continue
                
            estado = {
                'preenchido': False,
                'valor': '',
                'placeholder': ''
            }
            
            # Verificar se está nos campos já preenchidos globalmente
            if seletor in campos_preenchidos:
                estado['preenchido'] = True
                estado['valor'] = '(preenchido anteriormente)'
            else:
                # Verificar estado atual no DOM
                try:
                    seletor_escaped = seletor.replace('"', '\\"')
                    resultado = page.evaluate(f"""
                        () => {{
                            const el = document.querySelector("{seletor_escaped}");
                            if (!el) return null;
                            
                            return {{
                                valor: el.value || '',
                                placeholder: el.placeholder || '',
                                tipo: el.type || 'text'
                            }};
                        }}
                    """)
                    
                    if resultado:
                        estado['valor'] = resultado['valor']
                        estado['placeholder'] = resultado['placeholder']
                        
                        # Considerar preenchido se tem valor e não é apenas placeholder
                        if (resultado['valor'] and 
                            resultado['valor'].strip() and 
                            resultado['valor'] != resultado['placeholder']):
                            estado['preenchido'] = True
                            
                except Exception:
                    pass
            
            estado_campos[seletor] = estado
            
        except Exception as e:
            continue
    
    return estado_campos


def gerar_prompt_autonomo_completo(html, screenshot_path, instrucoes_customizadas, modelo, historico_acoes, page):
    """
    Gera prompt completo com TODOS os elementos interativos
    Para LLM decidir autonomamente em qualquer site
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remover elementos desnecessários
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # Extrair todos os elementos interativos
    elementos, contexto = extrair_elementos_interativos_completos(soup, page)
    
    if not elementos:
        print("[AVISO] Nenhum elemento interativo encontrado!")
        return None, []
    
    # Verificar estado atual dos campos de formulário
    seletores_campos = [elem["selector"] for elem in elementos if elem["tag"] in ["input", "select", "textarea"]]
    estado_campos = verificar_estado_campos_formulario(page, seletores_campos)
    
    # Gerar lista de seletores e elementos formatados
    seletores_validos = []
    lista_elementos = []
    
    for elem in elementos:
        seletor = elem["selector"]
        seletores_validos.append(seletor)
        
        # Formatar elemento para o LLM
        if elem["tag"] in ["input", "select", "textarea"]:
            # Campo de formulário
            estado = estado_campos.get(seletor, {})
            
            descricao = f"{elem['priority']} Campo: {elem.get('labelText', '') or elem.get('placeholder', '') or elem.get('name', '') or 'Campo'}"
            if elem.get("type"):
                descricao += f" (tipo: {elem['type']})"
            if elem.get("required"):
                descricao += " [OBRIGATÓRIO]"
            if elem["tag"] == "select" and elem.get("options"):
                descricao += f" - Opções: {', '.join(elem['options'][:3])}{'...' if len(elem['options']) > 3 else ''}"
            
            # Adicionar status de preenchimento
            if estado.get('preenchido'):
                descricao += " ✅ [JÁ PREENCHIDO]"
            else:
                descricao += " 📝 [DISPONÍVEL]"
                
            lista_elementos.append(f"{seletor} → {descricao}")
        
        elif elem["tag"] in ["button"] or elem.get("type") in ["submit", "button"]:
            # Botão
            descricao = f"{elem['priority']} Botão: {elem.get('text', 'Botão')}"
            lista_elementos.append(f"{seletor} → {descricao}")
        
        elif elem["tag"] == "a":
            # Link
            descricao = f"{elem['priority']} Link: {elem.get('text', 'Link')}"
            lista_elementos.append(f"{seletor} → {descricao}")
        
        else:
            # Outros elementos
            descricao = f"{elem['priority']} {elem['tag']}: {elem.get('text', 'Elemento')}"
            lista_elementos.append(f"{seletor} → {descricao}")
    
    # Montar lista formatada
    lista = "\n".join(lista_elementos)
    
    # Determinar se é modelo de visão
    is_vision_model = "vl" in modelo.lower() or "vision" in modelo.lower()
    image_content = None
    
    if is_vision_model and screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}"
                }
            }
    
    # Determinar objetivo
    if instrucoes_customizadas and instrucoes_customizadas.strip():
        objetivo = f"OBJETIVO CUSTOMIZADO: {instrucoes_customizadas.strip()}"
    else:
        objetivo = "OBJETIVO: Preencher formulários, realizar cadastros ou navegar conforme necessário"
    
    # Adicionar contexto da página
    contexto_texto = ""
    if contexto["sugestao"]:
        contexto_texto = f"\n🎯 CONTEXTO DA PÁGINA: {contexto['sugestao']}"
    
    # Construir histórico
    historico_texto = ""
    if historico_acoes and len(historico_acoes) > 0:
        historico_texto = "\n\nHISTÓRICO DE AÇÕES ANTERIORES:\n"
        for i, ac in enumerate(historico_acoes, 1):
            status = "✅ NAVEGOU" if ac.get('navegacao') else "⚡ MESMA PÁGINA"
            msg_res = f" | resultado: {ac.get('resultado', {}).get('message','')}" if ac.get('resultado') else ""
            historico_texto += f"{i}. [{ac.get('timestamp','')}] {ac.get('acao','')} → {status}{msg_res}\n"
            if ac.get('navegacao'):
                historico_texto += f"   URL: {ac.get('url_antes','')} → {ac.get('url_depois','')}\n"
        historico_texto += "\nCONSIDERE o progresso acima ao escolher a próxima ação.\n"
    
    # Adicionar estado dos campos
    campos_texto = ""
    campos_preenchidos_lista = [seletor for seletor, estado in estado_campos.items() if estado.get('preenchido')]
    campos_disponiveis_lista = [seletor for seletor, estado in estado_campos.items() if not estado.get('preenchido')]
    
    if campos_preenchidos_lista or campos_disponiveis_lista:
        campos_texto = "\n\n📋 ESTADO ATUAL DOS CAMPOS:\n"
        if campos_preenchidos_lista:
            campos_texto += f"✅ CAMPOS JÁ PREENCHIDOS: {', '.join(campos_preenchidos_lista)}\n"
        if campos_disponiveis_lista:
            campos_texto += f"📝 CAMPOS DISPONÍVEIS: {', '.join(campos_disponiveis_lista)}\n"
        campos_texto += "\n⚠️  FOQUE nos campos DISPONÍVEIS - NÃO repita campos já preenchidos!\n"
    
    # Prompt principal
    prompt_usuario = f"""
Você é um agente de automação web inteligente. Analise a página e escolha a melhor ação.

INSTRUÇÕES PARA AÇÃO AUTÔNOMA:
1. 🎯 EXECUTE **UMA ÚNICA AÇÃO** por resposta
2. 📋 ESCOLHA **APENAS** seletores da lista fornecida abaixo
3. ⚠️ Se precisar focar antes de digitar, envie um `{"action":"click","selector":"..."}` primeiro
4. ⚠️ Na **próxima resposta**, envie o `{"action":"fill","selector":"...","value":"..."}`
5. Para INPUT campos: use valores realistas e apropriados para o tipo
6. Para SENHAS: use senhas seguras (ex: "MinhaSenh@123")
7. Para CADASTRO: preencha TODOS os campos obrigatórios antes de enviar
8. 🚫 NUNCA repita ações em campos já preenchidos com SUCESSO (veja histórico)
9. ✅ Se um campo mostra "Fill OK", passe para o PRÓXIMO campo disponível
10. PRIORIZE elementos 🔥 sobre 📋

FORMATO DE RESPOSTA (JSON apenas):
- Para preencher: {{"action": "fill", "selector": "SELETOR_EXATO", "value": "valor_adequado"}}
- Para clicar: {{"action": "click", "selector": "SELETOR_EXATO"}}

🚨 CRÍTICO - FORMATO OBRIGATÓRIO:
• Responda com **UM ÚNICO JSON** válido na PRIMEIRA linha
• **ESCOLHA APENAS** entre os seletores listados abaixo
• NÃO use markdown (```json)
• NÃO adicione explicações
• NÃO quebre o JSON em múltiplas linhas
• Se o JSON não estiver exatamente válido, responda APENAS o JSON corrigido
• Use EXATAMENTE um dos seletores da lista abaixo

FLUXO CORRETO EXEMPLO:
1ª resposta: {"action":"click","selector":"[data-testid='auto-area-do-candidato-10']"}
2ª resposta: {"action":"fill","selector":"#login","value":"11380897700"}
3ª resposta: {"action":"fill","selector":"#senha","value":"Senha123"}
4ª resposta: {"action":"click","selector":"[data-testid='auto-entrar-3']"}

{objetivo}{contexto_texto}{historico_texto}{campos_texto}

ELEMENTOS DISPONÍVEIS NA PÁGINA:
{lista}

LEMBRE-SE: Sua resposta deve ser UM JSON VÁLIDO na primeira linha, exemplo:
{{"action": "fill", "selector": "#customer\\.firstName", "value": "João"}}

Com base na imagem{'(se disponível) ' if image_content else ''}e elementos listados, escolha a próxima ação mais apropriada:"""

    # Construir mensagens
    if image_content:
        messages = [
            {
                "role": "user",
                "content": [image_content, {"type": "text", "text": prompt_usuario}]
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": prompt_usuario
            }
        ]
    
    # Payload
    payload = {
        "model": modelo,
        "messages": messages,
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 2048,
        "stop": ["\n\n", "\r\n\r\n"]
    }
    
    return payload, seletores_validos


def gerar_prompt_otimizado_com_contexto(navegacao_llm, instrucoes_customizadas=None, historico_acoes=None):
    if not navegacao_llm:
        return None, []
    elementos_disponiveis = []
    seletores_validos = []
    for item in navegacao_llm["navegacao_principal"]:
        elementos_disponiveis.append(f"🧭 {item['texto']} → {item['seletor']}")
        seletores_validos.append(item['seletor'])
    for botao in navegacao_llm["elementos_interativos"]["botoes_principais"]:
        elementos_disponiveis.append(f"🔘 {botao['texto']} → {botao['seletor']}")
        seletores_validos.append(botao['seletor'])
    for secao in navegacao_llm["secoes_principais"]:
        if secao.get("acao"):
            elementos_disponiveis.append(f"📑 {secao['acao']['texto']} → {secao['acao']['seletor']}")
            seletores_validos.append(secao['acao']['seletor'])
    for item in navegacao_llm["concursos_ativos"]:
        if item.get("acao"):
            elementos_disponiveis.append(f"🎯 {item['acao']['texto']} ({item['nome']}) → {item['acao']['seletor']}")
            seletores_validos.append(item['acao']['seletor'])
    for input_elem in navegacao_llm["campos_formulario"]["inputs_texto"]:
        elementos_disponiveis.append(f"📝 {input_elem['nome']} (campo texto) → {input_elem['seletor']}")
        seletores_validos.append(input_elem['seletor'])
    for input_elem in navegacao_llm["campos_formulario"]["inputs_senha"]:
        elementos_disponiveis.append(f"🔒 {input_elem['nome']} (campo senha) → {input_elem['seletor']}")
        seletores_validos.append(input_elem['seletor'])
    for select_elem in navegacao_llm["campos_formulario"]["selects"]:
        elementos_disponiveis.append(f"📋 {select_elem['nome']} (seleção) → {select_elem['seletor']}")
        seletores_validos.append(select_elem['seletor'])
    for textarea_elem in navegacao_llm["campos_formulario"]["textareas"]:
        elementos_disponiveis.append(f"📄 {textarea_elem['nome']} (área texto) → {textarea_elem['seletor']}")
        seletores_validos.append(textarea_elem['seletor'])
    for botao_elem in navegacao_llm["campos_formulario"]["botoes_submit"]:
        elementos_disponiveis.append(f"✅ {botao_elem['texto']} (enviar) → {botao_elem['seletor']}")
        seletores_validos.append(botao_elem['seletor'])
    objetivo = instrucoes_customizadas if instrucoes_customizadas else "Navegar pelo site de forma eficiente para encontrar informações relevantes"
    url_atual = navegacao_llm['pagina']['url']
    is_login_page = ('login' in url_atual.lower() or 
                     any('login' in item['nome'].lower() for item in navegacao_llm['campos_formulario']['inputs_texto']) or
                     any('senha' in item['nome'].lower() for item in navegacao_llm['campos_formulario']['inputs_senha']))
    if is_login_page and instrucoes_customizadas and ('login' in instrucoes_customizadas.lower() or 'cpf' in instrucoes_customizadas.lower()):
        cpf_match = re.search(r'cpf[:\s]*(\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})', instrucoes_customizadas.lower())
        senha_match = re.search(r'senha[:\s]*(\S+)', instrucoes_customizadas.lower())
        cpf_valor = cpf_match.group(1).replace('.', '').replace('-', '') if cpf_match else "12345678901"
        senha_valor = senha_match.group(1) if senha_match else "senha123"
        elementos_essenciais = []
        seletores_essenciais = []
        for input_elem in navegacao_llm["campos_formulario"]["inputs_texto"]:
            elementos_essenciais.append(f"📝 PREENCHER {input_elem['nome']} com CPF → fill:{input_elem['seletor']}:{cpf_valor}")
            seletores_essenciais.append(input_elem['seletor'])
        for input_elem in navegacao_llm["campos_formulario"]["inputs_senha"]:
            elementos_essenciais.append(f"🔒 PREENCHER {input_elem['nome']} com senha → fill:{input_elem['seletor']}:{senha_valor}")
            seletores_essenciais.append(input_elem['seletor'])
        for botao in navegacao_llm["campos_formulario"]["botoes_submit"]:
            if botao["funcao"] == "login" or "entrar" in botao["texto"].lower():
                elementos_essenciais.append(f"✅ ENVIAR formulário via {botao['texto']} → submit:{botao['seletor']}")
                seletores_essenciais.append(botao['seletor'])
        if len(navegacao_llm["campos_formulario"]["inputs_senha"]) > 0:
            senha_seletor = navegacao_llm["campos_formulario"]["inputs_senha"][0]['seletor']
            elementos_essenciais.append(f"⌨️ PRESSIONAR Enter na senha → press:{senha_seletor}:Enter")
        elementos_disponiveis = elementos_essenciais
        seletores_validos = seletores_essenciais
        objetivo = f"{objetivo} - SEQUÊNCIA: 1) Preencher CPF 2) Preencher senha 3) Enviar formulário"
    contexto_pagina = f"Página: {navegacao_llm['pagina']['titulo']}"
    acoes_possiveis = "\n".join(navegacao_llm['contexto_para_llm']['acoes_possiveis'])
    lista_elementos = "\n".join(elementos_disponiveis)
    historico_texto = ""
    if historico_acoes and len(historico_acoes) > 0:
        historico_texto = "\n\nHISTÓRICO DE AÇÕES ANTERIORES:\n"
        for i, ac in enumerate(historico_acoes, 1):
            status = "✅ NAVEGOU" if ac.get('navegacao') else "⚡ MESMA PÁGINA"
            msg_res = f" | resultado: {ac.get('resultado', {}).get('message','')}" if ac.get('resultado') else ""
            historico_texto += f"{i}. [{ac.get('timestamp','')}] {ac.get('acao','')} → {status}{msg_res}\n"
            if ac.get('navegacao'):
                historico_texto += f"   URL: {ac.get('url_antes','')} → {ac.get('url_depois','')}\n"
        historico_texto += "\nCONSIDERE o progresso acima para escolher a próxima ação lógica.\n"
    prompt_usuario = f"""
Você é um agente de QA automatizado navegando no site: {navegacao_llm['pagina']['titulo']}.

CONTEXTO DA PÁGINA:
{contexto_pagina}

AÇÕES POSSÍVEIS IDENTIFICADAS:
{acoes_possiveis}{historico_texto}

OBJETIVO: {objetivo}

INSTRUÇÕES PARA LOGIN:
1. 🎯 EXECUTE **UMA ÚNICA AÇÃO** por resposta
2. 📋 ESCOLHA **APENAS** seletores da lista abaixo
3. PRIMEIRO: Preencha o campo de CPF/email usando fill:seletor:valor
4. SEGUNDO: Preencha o campo de senha usando fill:seletor:valor  
5. TERCEIRO: Envie o formulário usando submit:seletor ou press:seletor:Enter
6. Responda APENAS com JSON VÁLIDO na PRIMEIRA linha, sem markdown, sem ```
7. Use o SELECTOR EXATO da lista (não modifique)

🚨 FORMATO CRÍTICO: Resposta deve ser UM JSON na primeira linha!
🚨 **NÃO INVENTE SELETORES** - use apenas os listados abaixo!

AÇÕES DISPONÍVEIS:
- "fill": Para preencher campos (ex: {{"action": "fill", "selector": "#login", "value": "12345678901"}})
- "click": Para clicar em botões/links
- "submit": Para enviar formulário  
- "press": Para pressionar teclas (ex: {{"action": "press", "selector": "#senha", "value": "Enter"}})

FORMATO OBRIGATÓRIO:
{{"action": "AÇÃO", "selector": "SELETOR_EXATO", "value": "VALOR_SE_NECESSÁRIO"}}

ELEMENTOS DISPONÍVEIS:
{lista_elementos}

Com base no histórico e contexto, escolha a PRÓXIMA ação lógica:"""
    return prompt_usuario, seletores_validos
