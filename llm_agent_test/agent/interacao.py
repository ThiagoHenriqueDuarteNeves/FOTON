import logging
from agent.parser import extrair_json_da_resposta

# Histórico de seletores clicados e preenchidos durante a sessão
seletores_interagidos = set()

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

def preencher_campo(pagina, seletor, valor):
    try:
        el = pagina.locator(seletor).first
        el.wait_for(state="visible", timeout=5000)
        el.fill(valor)
        print(f"[📝] Preencheu o campo {seletor} com '{valor}'")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao preencher o campo {seletor}: {e}")
        return False

def executar_acao(pagina, resposta_llm):
    acao = extrair_json_da_resposta(resposta_llm)
    if not acao:
        print("[ERRO] Nenhum JSON válido encontrado na resposta:")
        print(resposta_llm)
        return

    seletor = acao.get("selector")
    if seletor in seletores_interagidos:
        print(f"[AVISO] Seletor já interagido: {seletor}, pulando para evitar repetição.")
        return

    if acao["action"] == "click":
        motivo = acao.get("motivo", "[Sem motivo informado]")
        print(f"[INFO] Motivo do clique: {motivo}")
        if clicar_elemento(pagina, seletor):
            seletores_interagidos.add(seletor)
            logging.info(f"Clique no seletor: {seletor} | Motivo: {motivo}")
        else:
            logging.error(f"Falha ao clicar no seletor: {seletor} | Motivo: {motivo}")

    elif acao["action"] == "fill":
        valor = acao.get("valor", "")
        if valor:
            if preencher_campo(pagina, seletor, valor):
                seletores_interagidos.add(seletor)
                logging.info(f"Preenchimento no seletor: {seletor} | Valor: {valor}")
            else:
                logging.error(f"Falha ao preencher o seletor: {seletor} | Valor: {valor}")
        else:
            print(f"[ERRO] Nenhum valor fornecido para preenchimento do campo: {seletor}")
