import requests
import time
from config import LLM_BACKEND, LLM_SERVERS  # Importa configurações

def chamar_llm(payload):
    if LLM_BACKEND == "lmstudio":
        return chamar_llm_lmstudio(payload)
    else:
        return chamar_llm_ollama(payload)

def chamar_llm_lmstudio(payload):
    print("\n⌛ Aguardando resposta do LLM (LM Studio)...")
    inicio = time.time()

    try:
        resposta = requests.post(
            LLM_SERVERS["lmstudio"],
            json=payload,
            timeout=None
        )

        duracao = round(time.time() - inicio, 2)
        print(f"✅ Resposta recebida após {duracao} segundos.")

        if not resposta.ok:
            print(f"[ERRO] Status HTTP {resposta.status_code}: {resposta.text}")
            return ""

        resposta_json = resposta.json()
        texto = resposta_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not texto:
            print("[⚠️ AVISO] O LLM respondeu, mas o campo 'content' está vazio.")
        else:
            print("[✔️ LLM] Resposta extraída com sucesso.")

        return texto

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao se comunicar com o LM Studio: {e}")
        return ""
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao processar a resposta do LM Studio: {e}")
        return ""

def chamar_llm_ollama(payload):
    print("[ERRO] suporte a chat/completions ainda não implementado para Ollama.")
    return ""
