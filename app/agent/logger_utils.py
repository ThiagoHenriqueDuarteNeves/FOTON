import re
import json

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
import os
import logging
from config import LOG_DIR, PRINT_DIR

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
