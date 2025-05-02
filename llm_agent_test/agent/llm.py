import requests
import time

BACKEND = "lmstudio"  # agora LM Studio é o padrão

def chamar_llm(prompt, modelo="mistral"):
    if BACKEND == "lmstudio":
        return chamar_llm_lmstudio(prompt)
    return chamar_llm_ollama(prompt, modelo)

def chamar_llm_ollama(prompt, modelo="mistral"):
    print("\n⌛ Aguardando resposta do LLM (Ollama)...")
    inicio = time.time()

    try:
        resposta = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            },
            timeout=None
        )

        duracao = round(time.time() - inicio, 2)
        print(f"✅ Resposta recebida após {duracao} segundos.")

        if not resposta.ok:
            print(f"[ERRO] Status HTTP {resposta.status_code}: {resposta.text}")
            return ""

        print("\n[DEBUG] Resposta completa recebida do LLM (bruta):")
        print(resposta.text)

        try:
            json_data = resposta.json()
            resposta_final = json_data.get("response", "").strip()
        except Exception as e:
            print(f"[ERRO] Falha ao interpretar JSON da resposta: {e}")
            return ""

        if not resposta_final:
            print("[⚠️ AVISO] O LLM respondeu, mas o campo 'response' está vazio.")
        else:
            print("[✔️ LLM] Resposta extraída com sucesso.")

        return resposta_final

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao se comunicar com o LLM: {e}")
        return ""
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao processar a resposta do LLM: {e}")
        return ""

def chamar_llm_lmstudio(prompt):
    print("\n⌛ Aguardando resposta do LLM (LM Studio)...")
    inicio = time.time()

    try:
        resposta = requests.post(
            "http://localhost:1234/v1/completions",
            json={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 800,
                "stop": None,
                "n": 1,
                "stream": False,
                "model": "local-model"
            },
            timeout=None
        )

        duracao = round(time.time() - inicio, 2)
        print(f"✅ Resposta recebida após {duracao} segundos.")

        if not resposta.ok:
            print(f"[ERRO] Status HTTP {resposta.status_code}: {resposta.text}")
            return ""

        print("\n[DEBUG] Resposta completa recebida do LLM (bruta):")
        print(resposta.text)

        try:
            json_data = resposta.json()
            resposta_final = json_data.get("choices", [{}])[0].get("text", "").strip()
        except Exception as e:
            print(f"[ERRO] Falha ao interpretar JSON da resposta: {e}")
            return ""

        if not resposta_final:
            print("[⚠️ AVISO] O LLM respondeu, mas o campo 'text' está vazio.")
        else:
            print("[✔️ LLM] Resposta extraída com sucesso.")

        return resposta_final

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Erro ao se comunicar com o LM Studio: {e}")
        return ""
    except Exception as e:
        print(f"[ERRO] Falha inesperada ao processar a resposta do LM Studio: {e}")
        return ""
