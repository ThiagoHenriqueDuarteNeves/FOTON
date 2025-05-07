import time
import logging
from pathlib import Path
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm
from agent.html_extractor import extrair_html, gerar_prompt_para_llm, seletores_interagidos
from agent.parser import extrair_json_da_resposta
from agent.interacao import executar_acao, fechar_aviso_de_cookies
from config import TARGET_URLS

# Configura log em arquivo
logging.basicConfig(
    filename='navegacao.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def salvar_screenshot(pagina, passo):
    Path("prints").mkdir(exist_ok=True)
    caminho = f"prints/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)
    print(f"[📸] Screenshot salva em: {caminho}")
    logging.info(f"Screenshot salva em: {caminho}")

def salvar_lista_de_seletores(html, passo):
    Path("logs").mkdir(exist_ok=True)
    caminho = f"logs/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        payload = gerar_prompt_para_llm(html)
        f.write(str(payload))
    print(f"[🧾] Lista de seletores salva em: {caminho}")
    logging.info(f"Lista de seletores salva em: {caminho}")

def agente_explorador(url, max_passos=10):
    navegador, pagina, playwright = iniciar_navegador()
    pagina.goto(url)
    pagina.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")

    seletores_visitados = set()

    for passo in range(max_passos):
        print(f"\n[PASSO {passo+1}]")
        logging.info(f"PASSO {passo+1}")

        try:
            # ✅ Espera genérica pelo carregamento da página
            pagina.wait_for_load_state("domcontentloaded")

            html = extrair_html(pagina)
            salvar_screenshot(pagina, passo + 1)
            salvar_lista_de_seletores(html, passo + 1)

            payload = gerar_prompt_para_llm(html)
            print("\n[DEBUG] Payload enviado ao LLM:")
            print(payload)

            resposta_llm = chamar_llm(payload)

            if not resposta_llm.strip():
                print("[LLM] <Resposta vazia>")
                logging.warning("LLM respondeu vazio")
                continue

            print("[✔️ LLM]", resposta_llm.strip())
            logging.info(f"Resposta LLM: {resposta_llm.strip()}")

            acao = extrair_json_da_resposta(resposta_llm)
            if acao and acao.get("selector") in seletores_visitados:
                print(f"[AVISO] Seletor já interagido: {acao.get('selector')}, pulando para evitar repetição.")
                logging.info(f"Seletor repetido ignorado: {acao.get('selector')}")
                continue

            if acao:
                seletor = acao.get("selector")
                seletores_visitados.add(seletor)
                seletores_interagidos.add(seletor)

            executar_acao(pagina, resposta_llm)
            time.sleep(2)

            if pagina.locator("#output").is_visible():
                print("[🎯] Formulário enviado com sucesso! Encerrando navegação.")
                logging.info("Formulário enviado com sucesso, encerrando.")
                break

        except Exception as e:
            print(f"[ERRO] Falha no passo {passo+1}: {e}")
            logging.error(f"Erro no passo {passo+1}: {e}")

    navegador.close()
    playwright.stop()
    print("\n[FIM] Navegação encerrada.")
    logging.info("Navegação encerrada.")

if __name__ == "__main__":
    agente_explorador(TARGET_URLS["cesgranrio"])
