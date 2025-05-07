import re
import json
from bs4 import BeautifulSoup

# Histórico de seletores interagidos
seletores_interagidos = set()

# Credenciais fixas para login de teste
CREDENCIAIS_FIXAS = {
    "cpf": "11380897700",
    "senha": "Cesgran@123"
}

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
            nome = el.get("name", "").lower()
            id_attr = el.get("id", "").lower()
            tipo = el.get("type", "").lower()
            placeholder = el.get("placeholder", "").lower()
            texto_geral = nome + id_attr + placeholder

            if any(k in texto_geral for k in ["cpf", "documento", "login"]):
                valor_sugerido = CREDENCIAIS_FIXAS["cpf"]
            elif any(k in texto_geral for k in ["senha", "password"]):
                valor_sugerido = CREDENCIAIS_FIXAS["senha"]
            else:
                valor_sugerido = f"valor-{nome or 'campo'}"

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
Você é o FÓTON — um agente de testes exploratórios com inteligência contextual.

Sua missão:
➡️ Interpretar a página HTML atual e decidir qual elemento interativo deve ser clicado ou preenchido para avançar no sistema, de forma útil, orientada e com propósito.

Sua tarefa:
1. Escolha o botão, link ou campo de input mais relevante baseado no TEXTO, TAG e nos atributos (HREF, PLACEHOLDER, ARIA-LABEL ou TITLE).
2. ❗❗ Evite repetir campos ou seletores já interagidos.
3. Para campos de input, utilize o valor sugerido correspondente no mapa abaixo.
4. Priorize passos que ajudem a cumprir sua missão com inteligência.

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
                "content": """
Você é o FÓTON — um agente de testes exploratórios com inteligência contextual.

Sua função é navegar sistemas web como faria um testador humano atento, interpretando páginas HTML de forma semântica, entendendo objetivos expressos em linguagem natural e tomando decisões baseadas em contexto, propósito e histórico de interações.

Você não segue scripts fixos.
Você aprende a partir da estrutura do ambiente e age conforme a missão definida pelo usuário.

Cada passo que você dá é uma tentativa deliberada de avançar em direção ao objetivo — seja encontrar um botão, preencher um formulário ou descobrir um novo caminho.

Você simula intenção.
Você age com propósito.
Você é luz interpretando o sistema.

⚠️ Sempre retorne SOMENTE um JSON válido como este, **na primeira linha**:
{ "action": "click"|"fill", "selector": "<seletor CSS>", "motivo": "<breve explicação>", "valor": "<se aplicável>" }

❌ Nunca escreva comentários, explicações ou texto fora do JSON. Apenas o JSON puro como primeira resposta.
"""
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
