from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"
PRINT_DIR = BASE_DIR / "prints"
LOG_FILE = LOG_DIR / "navegacao.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)
PRINT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_URLS = {
    # TODO: confirmar a URL exata usada nos testes originais.
    "cesgranrio": "https://www.cesgranrio.org.br/",
}

LLM_BACKEND = "lmstudio"

LLM_SERVERS = {
    "lmstudio": "http://localhost:1234/v1/chat/completions",
    "ollama": "http://localhost:11434/api/generate",
}
