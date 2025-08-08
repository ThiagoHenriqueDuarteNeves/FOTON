import json
import re
import os
import base64
from bs4 import BeautifulSoup

# Histórico de seletores já clicados durante a sessão
seletores_clicados = set()

def extrair_html(pagina):
    return pagina.content()

def gerar_prompt_em_chat_format(html, screenshot_path=None, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b"):
    soup = BeautifulSoup(html, "html.parser")
    elementos = []
    seletores_validos = []  # Lista para validação

    for el in soup.find_all(["button", "a", "input"]):
        texto = (el.text or el.get("value") or "").strip()
        seletor = gerar_selector(el)
        tag = el.name

        # Priorizar data-testid se existir
        testid = el.get("data-testid", "")
        if testid:
            seletor_preferido = f'[data-testid="{testid}"]'
        else:
            seletor_preferido = seletor

        # Extrair HREF especificamente
        href = el.get("href", "")
        
        # Extrair outros atributos
        extras = []
        for attr in ["type", "aria-label", "placeholder", "title"]:
            if el.has_attr(attr):
                extras.append(f'{attr.upper()}: "{el[attr]}"')
        extras_str = " | ".join(extras) if extras else ""

        if texto and seletor_preferido and seletor_preferido not in seletores_clicados:
            # Formato: [TEXTO: "...", SELECTOR: "...", TAG: ..., HREF: "...", TESTID: "..."]
            descricao = f'[TEXTO: "{texto}", SELECTOR: "{seletor_preferido}", TAG: {tag}, HREF: "{href}"'
            if testid:
                descricao += f', TESTID: "{testid}"'
            if extras_str:
                descricao += f', {extras_str}'
            descricao += ']'
            elementos.append(descricao)
            seletores_validos.append(seletor_preferido)

    lista = "\n".join(elementos) if elementos else "Nenhum elemento interativo encontrado."

    # Preparar imagem se screenshot fornecido
    image_content = None
    if screenshot_path and os.path.exists(screenshot_path):
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
        print(f"[🎯] Usando instruções customizadas: {instrucoes_customizadas[:50]}...")
    else:
        objetivo = "OBJETIVO: Navegar no site de concursos - escolha elementos que levem a informações sobre concursos, editais, inscrições, etc."

    prompt_usuario = f"""
Você é um agente de QA automatizado. Analise a imagem da página e a lista de elementos para escolher o mais relevante.

INSTRUÇÕES:
1. Olhe a imagem fornecida para ver os elementos visuais da página
2. Responda APENAS com um JSON VÁLIDO na PRIMEIRA linha, sem markdown, sem ``` e sem explicações
3. Escolha UM elemento da lista abaixo com base na IMAGEM e no OBJETIVO
4. Use o SELECTOR EXATO da lista (não modifique)
5. A resposta deve conter SOMENTE as chaves action e selector

{objetivo}

FORMATO OBRIGATÓRIO:
{{"action": "click", "selector": "SELETOR_EXATO_DA_LISTA"}}

ELEMENTOS DISPONÍVEIS:
{lista}

Baseado na imagem, escolha o elemento mais apropriado para o objetivo:"""

    # Construir mensagens com suporte a imagem
    messages = [
        {
            "role": "user",
            "content": []
        }
    ]
    
    # Adicionar imagem primeiro, se existir
    if image_content:
        messages[0]["content"].append(image_content)
        
    # Adicionar o prompt de texto depois
    messages[0]["content"].append({
        "type": "text",
        "text": prompt_usuario
    })
    
    payload = {
        "model": modelo,
        "messages": messages,
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 128000,  # Definido para 128k
        "stop": ["\n\n", "\r\n\r\n"]
    }
    
    return payload, seletores_validos

def gerar_selector(el):
    if el.has_attr("id"):
        return f'#{el["id"]}'
    elif el.has_attr("class"):
        classes = ".".join(el["class"]) 
        return f'.{classes}'
    elif el.name == "a":
        return "a"
    elif el.name == "button":
        return "button"
    return ""

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
                payload_retry = payload_original.copy()
                erro_msg = "ERRO: Responda SOMENTE com JSON válido na PRIMEIRA linha, sem markdown (sem ```)."
                
                if isinstance(payload_retry["messages"][-1]["content"], list):
                    # Formato multimodal
                    payload_retry["messages"][-1]["content"][0]["text"] += f"\n\n{erro_msg}"
                else:
                    # Formato texto
                    payload_retry["messages"][-1]["content"] += f"\n\n{erro_msg}"
                
                resposta_llm = chamar_llm_func(payload_retry)
                continue
            else:
                return None
        
        seletor = acao.get("selector", "")
        
        if seletor in seletores_validos:
            print(f"[✅] Seletor válido encontrado: {seletor}")
            return acao
        else:
            print(f"[⚠️] Tentativa {tentativa + 1}: Seletor inválido '{seletor}' não está na lista")
            if tentativa < max_tentativas - 1:
                # Retry com mensagem específica
                payload_retry = payload_original.copy()
                erro_msg = f"ERRO: O seletor '{seletor}' não está na lista. Responda com um dos SELECTORs fornecidos, copiado verbatim, sem markdown."
                
                if isinstance(payload_retry["messages"][-1]["content"], list):
                    # Formato multimodal
                    payload_retry["messages"][-1]["content"][0]["text"] += f"\n\n{erro_msg}"
                else:
                    # Formato texto
                    payload_retry["messages"][-1]["content"] += f"\n\n{erro_msg}"
                
                resposta_llm = chamar_llm_func(payload_retry)
                continue
    
    print(f"[❌] Falha após {max_tentativas} tentativas. Nenhum seletor válido encontrado.")
    return None

def extrair_json_da_resposta(resposta_llm):
    try:
        # Limpar a resposta - pegar apenas a primeira linha
        primeira_linha = resposta_llm.split('\n')[0].strip()
        
        # Tentar encontrar JSON na primeira linha
        matches = re.findall(r'\{[^{}]*\}', primeira_linha)
        for m in matches:
            try:
                json_obj = json.loads(m)
                if "action" in json_obj and "selector" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                continue
                
        # Se não encontrou, tentar em toda a resposta como fallback
        matches = re.findall(r'\{[^{}]*\}', resposta_llm)
        for m in matches:
            try:
                json_obj = json.loads(m)
                if "action" in json_obj and "selector" in json_obj:
                    return json_obj
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        print(f"[DEBUG] Erro ao extrair JSON: {e}")
        
    return None

def fechar_aviso_de_cookies(pagina):
    possiveis_botoes = [
        "text=Aceito", "text=Aceitar", "text=OK", "text=Entendi", "text=Concordo"
    ]
    for seletor in possiveis_botoes:
        try:
            pagina.locator(seletor).first.click(timeout=1000)
            print(f"[INFO] Fechou aviso de cookies com seletor: {seletor}")
            return
        except:
            continue
    print("[INFO] Nenhum aviso de cookies foi encontrado ou já estava fechado.")

def salvar_lista_seletores(elementos, passo):
    os.makedirs("logs", exist_ok=True)
    caminho = f"logs/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(elementos))
    print(f"[INFO] Lista de seletores salva em: {caminho}")
    import logging
    logging.info(f"Lista de seletores salva em: {caminho}")

def salvar_screenshot(pagina, passo):
    os.makedirs("prints", exist_ok=True)
    caminho = f"prints/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)
    print(f"[INFO] Screenshot salva em: {caminho}")
    import logging
    logging.info(f"Screenshot salva em: {caminho}")

def executar_acao(pagina, resposta_llm):
    acao = extrair_json_da_resposta(resposta_llm)
    if not acao:
        print("[ERRO] Nenhum JSON válido encontrado na resposta:")
        print(resposta_llm)
        return

    seletor = acao.get("selector")
    if seletor in seletores_clicados:
        print(f"[AVISO] Seletor já visitado: {seletor}, pulando para evitar repetição.")
        return

    try:
        if acao["action"] == "click":
            el = pagina.locator(seletor).first

            try:
                # Escapar aspas duplas no seletor para JavaScript
                seletor_escaped = seletor.replace('"', '\\"')
                
                pagina.evaluate(f'''
                    () => {{
                        const el = document.querySelector("{seletor_escaped}");
                        if (el) {{
                            el.scrollIntoView({{ behavior: "smooth", block: "center" }});
                        }}
                    }}
                ''')
                pagina.wait_for_timeout(300)
                print(f"[INFO] Rolou até o seletor: {seletor}")
            except:
                print(f"[⚠️ AVISO] Não conseguiu rolar até o seletor: {seletor}")

            try:
                el.wait_for(state="visible", timeout=5000)
                el.click()
                print(f"[INFO] Clicou normalmente no seletor: {seletor}")
                import logging
                logging.info(f"Clicou normalmente no seletor: {seletor}")
                seletores_clicados.add(seletor)
                return
            except Exception as e:
                print(f"[⚠️ AVISO] Clique padrão falhou: {e}")
                print("[INFO] Tentando clique forçado no DOM com JavaScript...")

            # Escapar aspas duplas no seletor para JavaScript
            seletor_escaped = seletor.replace('"', '\\"')
            
            sucesso = pagina.evaluate(f'''
                () => {{
                    const el = document.querySelector("{seletor_escaped}");
                    if (el) {{
                        el.click();
                        return true;
                    }}
                    return false;
                }}
            ''')
            if sucesso:
                print(f"[✔️] Clique forçado por JavaScript bem-sucedido.")
                import logging
                logging.info(f"Clique forçado por JavaScript no seletor: {seletor}")
                seletores_clicados.add(seletor)
            else:
                print(f"[ERRO] Falha ao executar clique via JavaScript.")
                import logging
                logging.error(f"Falha no clique via JavaScript para seletor: {seletor}")
    except Exception as e:
        print(f"[ERRO] Falha ao executar ação final: {e}")
        import logging
        logging.error(f"Erro durante execução da ação final: {e}")
