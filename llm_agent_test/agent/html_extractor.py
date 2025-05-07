import re
import json
from bs4 import BeautifulSoup

# Histórico de seletores interagidos
seletores_interagidos = set()

def extrair_html(pagina):
    return pagina.content()

def gerar_prompt_para_llm(html):
    soup = BeautifulSoup(html, "html.parser")
    elementos = []
    valores_sugeridos = {}
    preenchidos = list(seletores_interagidos)

    for el in soup.find_all(["button", "a", "input"]):
        texto = (el.text or el.get("value") or el.get("placeholder") or "").strip()
        seletor = gerar_seletor_css(el)
        tag = el.name

        if not seletor or seletor in seletores_interagidos:
            continue

        extras = []
        for attr in ["href", "type", "aria-label", "placeholder", "title"]:
            if el.has_attr(attr):
                extras.append(f'{attr.upper()}: "{el[attr]}"')

        if tag == "input":
            valor_sugerido = f"valor-{el.get('name', 'campo')}"
            extras.append(f'VALOR_SUGERIDO: "{valor_sugerido}"')
            valores_sugeridos[seletor] = valor_sugerido

        extras_str = " | ".join(extras)
        descricao = f'TEXTO: "{texto}" | SELECTOR: {seletor} | TAG: {tag}'
        if extras_str:
            descricao += f' | {extras_str}'

        elementos.append(descricao)

    lista = "\n".join(elementos) if elementos else "Nenhum elemento interativo encontrado."
    mapa_valores = "\n".join([f'- {k}: "{v}"' for k, v in valores_sugeridos.items()]) or "Nenhum valor sugerido."

    prompt_usuario = f"""
Você é um agente de QA automatizado.

Sua tarefa:
1. Escolha o botão, link ou campo de input mais relevante baseado no TEXTO, TAG e nos atributos (HREF, PLACEHOLDER, ARIA-LABEL ou TITLE).
2. ❗❗ Evite repetir campos ou seletores já interagidos.
3. Para campos de input, utilize o valor sugerido correspondente no mapa abaixo.

Campos já interagidos:
{json.dumps(preenchidos, ensure_ascii=False)}

Mapa de valores sugeridos:
{mapa_valores}

⚠️ ATENÇÃO:
- ✅ Retorne SOMENTE um JSON como este, na PRIMEIRA LINHA da resposta:
{{ "action": "click"|"fill", "selector": "<seletor CSS>", "motivo": "<explicação breve da escolha>", "valor": "<valor se for fill>" }}

❌ NÃO escreva explicações fora do JSON.
❌ NÃO inclua comentários, textos ou linhas extras.

Lista de elementos interativos:
{lista}
"""

    return {
        "model": "qwen2.5-7b-instruct-uncensored",
        "messages": [
            {
                "role": "system",
                "content": "Você é um agente de QA automatizado. Retorne apenas o JSON na primeira linha como solicitado. Procure interagir com elementos que levem à navegação ou preenchimento útil."
            },
            {
                "role": "user",
                "content": prompt_usuario
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": False,
        "language": "pt-BR"
    }

def gerar_seletor_css(el):
    if el.has_attr("id"):
        return f'#{el["id"]}'
    elif el.has_attr("class"):
        return f'.{".".join(el["class"])}'
    elif el.name == "a":
        return "a"
    elif el.name == "button":
        return "button"
    elif el.name == "input":
        return "input"
    return ""
