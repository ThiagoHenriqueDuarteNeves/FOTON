import json
import re
import os
from bs4 import BeautifulSoup

# Histórico de seletores já clicados durante a sessão
seletores_clicados = set()

def extrair_html(pagina):
    return pagina.content()

def gerar_prompt_em_chat_format(html):
    soup = BeautifulSoup(html, "html.parser")
    elementos = []

    for el in soup.find_all(["button", "a", "input"]):
        texto = (el.text or el.get("value") or "").strip()
        seletor = gerar_selector(el)
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
1. Escolha o botão ou link mais relevante baseado no TEXTO, na TAG, e nos atributos (como HREF, PLACEHOLDER, ARIA-LABEL ou TITLE).
⚠️ ATENÇÃO:
- ❌ NÃO escreva nenhuma explicação, comentários ou conteúdo adicional.
- ✅ Escreva SOMENTE um JSON como este, na PRIMEIRA LINHA da resposta:

{{ "action": "click", "selector": ".btn.btn-primary.fw-bold" }}

❌ NÃO inclua mais nada após essa linha. Isso é OBRIGATÓRIO.

Formato esperado:
{{ "action": "click", "selector": "<seletor CSS>" }}

Lista de elementos interativos:
{lista}
"""

    return {
        "model": "qwen2.5-7b-instruct-uncensored",
        "messages": [
            {
                "role": "system",
                "content": "Você é um agente de QA automatizado. Retorne apenas o JSON na primeira linha como solicitado."
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
