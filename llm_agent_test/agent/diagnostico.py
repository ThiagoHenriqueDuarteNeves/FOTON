import requests
from config import LLM_SERVERS

def testar_llm(modelo="mistral", prompt="Diga Olá"):
    try:
        resposta = requests.post(
            LLM_SERVERS["ollama"],
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            }
        )

        json_resp = resposta.json()
        print("\n✅ Resposta recebida do Ollama:")
        print(json_resp)

    except requests.exceptions.ConnectionError:
        print("\n❌ Não foi possível se conectar ao Ollama. Verifique se o servidor está rodando.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    testar_llm()
