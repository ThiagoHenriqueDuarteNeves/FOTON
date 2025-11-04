"""Runner module executed in a separate process to drive the web agent.

Usage:
    python -m backend.runner <config_json_path>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m backend.runner <caminho_config.json>", file=sys.stderr)
        sys.exit(1)

    config_path = Path(sys.argv[1]).resolve()
    try:
        config = load_config(config_path)
    finally:
        try:
            config_path.unlink()
        except OSError:
            pass

    from main import navegar_com_agente

    navegar_com_agente(**config)


if __name__ == "__main__":
    main()
