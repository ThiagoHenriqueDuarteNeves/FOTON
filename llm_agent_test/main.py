import time
import logging
from datetime import datetime
from pathlib import Path
from agent.browser import iniciar_navegador
from agent.llm import chamar_llm_lmstudio  # LM Studio como padrão
from agent.testid_injector import injetar_data_testids  # Novo injetor
from agent.utils import (
    extrair_html,
    gerar_prompt_em_chat_format,
    executar_acao,
    fechar_aviso_de_cookies,
    extrair_json_da_resposta,  # Usar a função padrão
    validar_seletor_e_retry  # Nova função de validação
)
import requests

# Configura log em arquivo
logging.basicConfig(
    filename='navegacao.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def obter_modelos_disponiveis():
    """Obtém a lista de modelos disponíveis do LM Studio"""
    try:
        print("[INFO] Obtendo lista de modelos do LM Studio...")
        resposta = requests.get("http://localhost:1234/v1/models", timeout=5)
        resposta.raise_for_status()
        
        dados = resposta.json()
        modelos = []
        
        if "data" in dados:
            for modelo in dados["data"]:
                if "id" in modelo:
                    modelos.append(modelo["id"])
        
        print(f"[INFO] Modelos encontrados: {modelos}")
        return modelos
        
    except requests.exceptions.ConnectionError:
        print("[AVISO] LM Studio não está disponível. Usando modelos padrão.")
        return [
            "qwen/qwen2.5-vl-7b",
            "gpt-4-vision-preview", 
            "claude-3-5-sonnet-20241022",
            "llava-v1.6-34b",
            "minicpm-v-2_6"
        ]
    except Exception as e:
        print(f"[ERRO] Falha ao obter modelos: {e}")
        return ["qwen/qwen2.5-vl-7b"]  # Modelo padrão como fallback

def salvar_screenshot(pagina, passo):
    Path("prints").mkdir(exist_ok=True)
    caminho = f"prints/passo_{passo}.png"
    pagina.screenshot(path=caminho, full_page=True)
    print(f"[📸] Screenshot salva em: {caminho}")
    logging.info(f"Screenshot salva em: {caminho}")

def salvar_lista_de_seletores(html, passo, screenshot_path=None, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b"):
    Path("logs").mkdir(exist_ok=True)
    caminho = f"logs/seletores_passo_{passo}.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        payload, seletores_validos = gerar_prompt_em_chat_format(html, screenshot_path, instrucoes_customizadas, modelo)
        f.write(str(payload))
    print(f"[🧾] Lista de seletores salva em: {caminho}")
    logging.info(f"Lista de seletores salva em: {caminho}")
    return payload, seletores_validos

def chamar_llm_openai_style(payload):
    try:
        modelo_usado = payload.get('model', 'modelo-desconhecido')
        print(f"[DEBUG] Enviando request para: http://localhost:1234/v1/chat/completions")
        print(f"[DEBUG] Usando modelo: {modelo_usado}")
        
        resposta = requests.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=60)
        
        print(f"[DEBUG] Status code: {resposta.status_code}")
        print(f"[DEBUG] Response headers: {resposta.headers}")
        
        resposta.raise_for_status()
        retorno = resposta.json()
        
        print(f"[DEBUG] Response JSON keys: {retorno.keys()}")
        
        if "choices" in retorno and len(retorno["choices"]) > 0:
            content = retorno["choices"][0]["message"]["content"]
            print(f"[DEBUG] Content extraído: '{content}'")
            return content
        else:
            print(f"[DEBUG] Estrutura inesperada: {retorno}")
            return ""
            
    except Exception as e:
        print(f"[ERRO] Falha na chamada LLM: {e}")
        return ""

def agente_explorador(url, max_passos=5, instrucoes_customizadas=None, modelo="qwen/qwen2.5-vl-7b"):
    # Verificar se há uma instância da UI para controle de parada
    def check_stop_requested():
        try:
            from ui_agente import current_ui_instance
            return current_ui_instance and current_ui_instance.is_stop_requested()
        except:
            return False
    
    navegador, pagina, playwright = iniciar_navegador()
    pagina.goto(url)

    # Maximiza a janela após abertura
    pagina.evaluate("window.moveTo(0, 0); window.resizeTo(screen.width, screen.height);")

    fechar_aviso_de_cookies(pagina)
    
    # Injetar data-testids únicos para melhor estabilidade
    injetar_data_testids(pagina)
    
    seletores_visitados = set()

    for passo in range(max_passos):
        # Verificar se foi solicitada a parada
        if check_stop_requested():
            print("🛑 Execução interrompida pelo usuário")
            logging.info("Execução interrompida pelo usuário")
            break
            
        print(f"\n[PASSO {passo+1}]")
        logging.info(f"PASSO {passo+1}")

        try:
            html = extrair_html(pagina)

            # Salvar screenshot primeiro
            salvar_screenshot(pagina, passo + 1)
            screenshot_path = f"prints/passo_{passo + 1}.png"
            
            # Gerar payload com screenshot e obter seletores válidos
            payload, seletores_validos = salvar_lista_de_seletores(html, passo + 1, screenshot_path, instrucoes_customizadas, modelo)

            print("\n[DEBUG] Payload enviado ao LLM:")
            print(f"Modelo: {payload['model']}")
            print(f"Temperature: {payload['temperature']}")
            print(f"Max tokens: {payload['max_tokens']}")
            print(f"Stop tokens: {payload['stop']}")
            print(f"Seletores válidos: {len(seletores_validos)}")

            # Primeira tentativa
            resposta_llm = chamar_llm_openai_style(payload)

            if not resposta_llm.strip():
                print("[LLM] <Resposta vazia>")
                logging.warning("LLM respondeu vazio")
                continue

            print("[✔️ LLM]", resposta_llm.strip())
            logging.info(f"Resposta LLM: {resposta_llm.strip()}")

            # Validação com retry
            acao = validar_seletor_e_retry(resposta_llm, seletores_validos, chamar_llm_openai_style, payload)
            
            if not acao:
                print("[ERRO] Falha na validação do seletor após todas as tentativas")
                logging.error("Falha na validação do seletor")
                continue

            # Verificar novamente se foi solicitada a parada antes de executar ação
            if check_stop_requested():
                print("🛑 Execução interrompida pelo usuário antes da ação")
                logging.info("Execução interrompida pelo usuário antes da ação")
                break

            if acao.get("action") == "click":
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
    # O entry point agora chama a UI diretamente.
    from ui_agente import main as ui_main
    ui_main()

