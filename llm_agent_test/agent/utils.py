import json
import re
import os
import logging
from bs4 import BeautifulSoup
from config import LOG_DIR, PRINT_DIR

# Histórico de seletores já clicados durante a sessão
seletores_clicados = set()

def extrair_html(pagina):
    return pagina.content()

def gerar_prompt_para_llm(html):
    """
    Monta o payload no formato chat para o LLM com base nos elementos interativos da página.
    """
    soup = BeautifulSoup(html, "html.parser")
    elementos = []

    for el in soup.find_all(["button", "a", "input"]):
        texto = (el.text or el.get("value") or "").strip()
        seletor = gerar_seletor_css(el)
        tag = el.name

        extras = []
        for attr in ["href", "type", "aria-label", "placeholder", "title"]:
            if el.has_attr(attr):
                extras.append(f'{attr.upper()}: "{el[attr]}"')
        extras_str = " | ".join(extras)

        if texto and seletor and seletor not in seletores_clicados:
            descricao = f'TEXTO: "{texto}" | SELECTOR: {seletor} | TAG: {tag}'
            if extras_str:
                descricao += f' | {extras_str}'
            elementos.append(descricao)

    lista = "\n".join(elementos) if elementos else "Nenhum elemento interativo encontrado."

    prompt_usuario = f"""
Você é um agente de QA automatizado.

Sua tarefa:
1. Escolha o botão ou link mais relevante baseado no TEXTO, na TAG e nos atributos (como HREF, PLACEHOLDER, ARIA-LABEL ou TITLE).
2. Explique brevemente o motivo da escolha para fins de auditoria.

⚠️ ATENÇÃO:
- ✅ Retorne SOMENTE um JSON como este, na PRIMEIRA LINHA da resposta:
{{ "action": "click", "selector": "<seletor CSS>", "motivo": "<explicação breve da escolha>" }}

❌ NÃO escreva explicações fora do JSON.
❌ NÃO inclua comentários, textos ou linhas extras.

Formato obrigatório:
{{ "action": "click", "selector": "<seletor CSS>", "motivo": "<frase breve>" }}

Lista de elementos interativos:
{lista}
"""

    return {
        "model": "qwen2.5-7b-instruct-uncensored",
        "messages": [
            {
                "role": "system",
                "content": "Você é um agente de QA automatizado. Retorne apenas o JSON na primeira linha como solicitado. procure utilizar botoes que façam voce navegar pelas paginas de concursos"
            },
            {
                "role": "user",
                "content": prompt_usuario
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": False,
        "language": "pt-BR"
    }

def gerar_seletor_css(el):
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

def extrair_json_da_resposta(resposta_llm):
    try:
        matches = re.findall(r'\{[^{}]*\}', resposta_llm)
        for m in matches:
            json_obj = json.loads(m)
            if "action" in json_obj and "selector" in json_obj:
                return json_obj
    except Exception:
        pass
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
    os.makedirs(LOG_DIR, exist_ok=True)
    caminho = f"{LOG_DIR}/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(elementos))
    print(f"[INFO] Lista de seletores salva em: {caminho}")
    logging.info(f"Lista de seletores salva em: {caminho}")

def salvar_screenshot(pagina, passo):
    os.makedirs(PRINT_DIR, exist_ok=True)
    caminho = f"{PRINT_DIR}/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)
    print(f"[INFO] Screenshot salva em: {caminho}")
    logging.info(f"Screenshot salva em: {caminho}")

def executar_acao(pagina, resposta_llm):
    acao = extrair_json_da_resposta(resposta_llm)
    if not acao:
        print("[ERRO] Nenhum JSON válido encontrado na resposta:")
        print(resposta_llm)
        return

    seletor = acao.get("selector")
    motivo = acao.get("motivo", "[Sem motivo informado]")

    if seletor in seletores_clicados:
        print(f"[AVISO] Seletor já visitado: {seletor}, pulando para evitar repetição.")
        return

    print(f"[INFO] Motivo da escolha: {motivo}")

    try:
        if acao["action"] == "click":
            if clicar_elemento(pagina, seletor):
                seletores_clicados.add(seletor)
                logging.info(f"Clique no seletor: {seletor} | Motivo: {motivo}")
            else:
                logging.error(f"Falha ao clicar no seletor: {seletor} | Motivo: {motivo}")
    except Exception as e:
        print(f"[ERRO] Falha ao executar ação final: {e}")
        logging.error(f"Erro durante execução da ação final: {e}")

def clicar_elemento(pagina, seletor):
    try:
        el = pagina.locator(seletor).first

        pagina.evaluate(f'''
            () => {{
                const el = document.querySelector("{seletor}");
                if (el) {{
                    el.scrollIntoView({{ behavior: "smooth", block: "center" }});
                }}
            }}
        ''')
        pagina.wait_for_timeout(300)
        print(f"[INFO] Rolou até o seletor: {seletor}")

        el.wait_for(state="visible", timeout=5000)
        el.click()
        print(f"[INFO] Clicou normalmente no seletor: {seletor}")
        return True

    except Exception as e:
        print(f"[⚠️ AVISO] Clique padrão falhou: {e}")
        print("[INFO] Tentando clique forçado no DOM com JavaScript...")

        sucesso = pagina.evaluate(f'''
            () => {{
                const el = document.querySelector("{seletor}");
                if (el) {{
                    el.click();
                    return true;
                }}
                return false;
            }}
        ''')

        if sucesso:
            print(f"[✔️] Clique forçado por JavaScript bem-sucedido.")
            return True

        print(f"[ERRO] Falha ao executar clique via JavaScript.")
        return False
