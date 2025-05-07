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
