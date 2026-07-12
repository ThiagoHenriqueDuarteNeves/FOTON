# FOTON

Agente autônomo de exploração de sites guiado por um LLM local. Em vez de depender de seletores fixos escritos à mão, o agente lê a página atual, pergunta a um modelo de linguagem rodando localmente (LM Studio ou Ollama) qual elemento clicar em seguida e executa a ação via Playwright — registrando screenshot e seletores candidatos a cada passo. Pensado como experimento de automação exploratória / QA guiada por LLM, não como framework de testes pronto para produção.

## Como funciona

O agente roda em loop, repetindo o seguinte ciclo a cada passo:

1. **Extrai o HTML** da página atual (`agent/browser.py` cuida da navegação via Playwright).
2. **Identifica elementos interativos** (`button`, `a`, `input`) com BeautifulSoup, coletando texto, tag e atributos relevantes (`href`, `type`, `aria-label`, `placeholder`, `title`) — ver `agent/utils.py`.
3. **Monta um prompt** pedindo ao LLM para escolher o próximo elemento a clicar e justificar a escolha, retornando um JSON no formato `{"action": "click", "selector": "...", "motivo": "..."}`.
4. **Envia o prompt ao LLM** configurado (`agent/llm.py`), que hoje suporta o backend LM Studio (API compatível com chat/completions da OpenAI).
5. **Faz o parse da resposta**, extraindo o JSON da primeira linha útil da saída do modelo.
6. **Executa o clique** via Playwright: rola o elemento até a área visível e clica; se o clique padrão falhar, tenta um clique forçado via JavaScript (`el.click()` direto no DOM) como fallback.
7. **Registra o passo**: salva um screenshot da página (`prints/passo_N.png`) e a lista de seletores candidatos daquele passo (`logs/seletores_passo_N.txt`), além de logar tudo em `navegacao.log`.
8. Evita clicar duas vezes no mesmo seletor dentro da mesma sessão (histórico mantido em memória).

## Pré-requisitos

- Python 3.x
- Um servidor de LLM local rodando:
  - **LM Studio**, com API compatível OpenAI exposta em `http://localhost:1234/v1/chat/completions`, ou
  - **Ollama**, exposto em `http://localhost:11434/api/generate`
  - O backend usado é escolhido pela variável `LLM_BACKEND` em `config.py`
- Navegador do Playwright instalado (Chromium)

## Como executar

```bash
cd llm_agent_test
pip install -r requirements.txt
playwright install chromium
python main.py
```

`main.py` inicia o agente contra a URL definida em `TARGET_URLS["cesgranrio"]` (ver seção de configuração abaixo).

## Configuração

Tudo fica centralizado em `llm_agent_test/config.py`:

- `TARGET_URLS` — dicionário com as URLs alvo disponíveis; confira/ajuste a URL desejada antes de rodar.
- `LLM_BACKEND` — define qual backend usar (`"lmstudio"` ou `"ollama"`).
- `LLM_SERVERS` — endereços dos servidores de cada backend.
- `LOG_DIR`, `PRINT_DIR`, `LOG_FILE` — diretórios/arquivo de saída da execução.

## Saída

Toda a saída é gerada em tempo de execução e não é versionada:

- `llm_agent_test/prints/` — screenshots de cada passo (`passo_N.png`)
- `llm_agent_test/logs/` — lista de seletores candidatos por passo (`seletores_passo_N.txt`)
- `llm_agent_test/navegacao.log` — log textual da execução (cliques, erros, motivos escolhidos pelo LLM)

## Estrutura do projeto

```
llm_agent_test/
├── main.py                 # entrypoint: roda o agente contra a URL alvo
├── config.py                # URLs alvo, backend do LLM, diretórios de saída
├── requirements.txt
└── agent/
    ├── __init__.py
    ├── browser.py           # inicialização do navegador/contexto Playwright
    ├── llm.py                # chamada ao LLM (LM Studio / Ollama)
    ├── utils.py              # extração de HTML, montagem de prompt, execução de cliques, logging
    └── diagnostico.py        # script avulso para testar conexão com o Ollama
```

## Limitações conhecidas

- O suporte ao backend **Ollama** ainda não está implementado de fato (`chamar_llm_ollama` apenas retorna erro); na prática, hoje só o LM Studio funciona.
- O agente depende inteiramente de um LLM local rodando para funcionar — não há fallback nem modo offline. Sem LM Studio (ou, futuramente, Ollama) ativo na porta configurada, o loop não avança.
- A qualidade da navegação depende diretamente da qualidade das respostas do modelo local escolhido; não há garantia de que o LLM sempre escolha um elemento útil ou retorne um JSON bem formado (há tratamento de erro, mas não recuperação inteligente).
- Projeto experimental/pessoal para explorar a combinação de agentes LLM com automação de navegador — não é uma ferramenta de testes pronta para uso em produção.
