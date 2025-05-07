from pathlib import Path

# Diretórios de logs e prints
LOG_DIR = Path("logs")
PRINT_DIR = Path("prints")
LOG_FILE = LOG_DIR / "navegacao.log"

# URLs de destino
TARGET_URLS = {
    "cesgranrio": "https://caixa.cesgranrio.org.br/"
}

# Backend atual do LLM (lmstudio ou ollama)
LLM_BACKEND = "lmstudio"

# Portas dos servidores locais dos LLMs
LLM_PORTS = {
    "lmstudio": 1234,
    "ollama": 11434
}

# Modelos usados por backend
LLM_MODELS = {
    "lmstudio": "local-model",
    "ollama": "mistral"
}

# Endpoints dos LLMs
LLM_SERVERS = {
    "lmstudio": "http://localhost:1234/v1/chat/completions",
    "ollama": "http://localhost:11434/api/generate"
}
