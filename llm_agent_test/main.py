import time
import logging
from datetime import datetime
from pathlib import Path
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_lmstudio  # LM Studio como padrão
from agent.utils import (
    extrair_html,
    gerar_prompt,
    executar_acao,
    fechar_aviso_de_cookies,
    extrair_json_da_resposta
)

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
        prompt = gerar_prompt(html)
        f.write(prompt)
    print(f"[🧾] Lista de seletores salva em: {caminho}")
    logging.info(f"Lista de seletores salva em: {caminho}")

def agente_explorador(url, max_passos=5):
    chamar_llm = chamar_llm_lmstudio  # Definido fixo

    navegador, pagina, playwright = iniciar_navegador()
    pagina.goto(url)

    # Maximiza a janela após abertura
    pagina.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")

    fechar_aviso_de_cookies(pagina)
    seletores_visitados = set()

    for passo in range(max_passos):
        print(f"\n[PASSO {passo+1}]")
        logging.info(f"PASSO {passo+1}")

        try:
            html = extrair_html(pagina)

            salvar_screenshot(pagina, passo + 1)
            salvar_lista_de_seletores(html, passo + 1)

            prompt = gerar_prompt(html)

            print("\n[DEBUG] Prompt enviado ao LLM:")
            print(prompt[:1000])

            resposta_llm = chamar_llm(prompt)

            if not resposta_llm.strip():
                print("[LLM] <Resposta vazia>")
                logging.warning("LLM respondeu vazio")
                continue

            print("[✔️ LLM]", resposta_llm.strip())
            logging.info(f"Resposta LLM: {resposta_llm.strip()}")

            acao = extrair_json_da_resposta(resposta_llm)
            if acao and acao.get("action") == "click":
                seletor = acao.get("selector")
                if seletor in seletores_visitados:
                    print(f"[AVISO] Seletor já visitado: {seletor}, pulando para evitar repetição.")
                    logging.info(f"Seletor repetido ignorado: {seletor}")
                    continue
                seletores_visitados.add(seletor)

            executar_acao(pagina, resposta_llm)
            time.sleep(2)

        except Exception as e:
            print(f"[ERRO] Falha no passo {passo+1}: {e}")
            logging.error(f"Erro no passo {passo+1}: {e}")

    navegador.close()
    playwright.stop()
    print("\n[FIM] Navegação encerrada.")
    logging.info("Navegação encerrada.")

if __name__ == "__main__":
    agente_explorador("https://concursos.cesgranrio.org.br/portal")
