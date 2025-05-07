Fóton – Explorador de Sistemas com IA

Testes não precisam ser rígidos. Eles podem explorar, adaptar e aprender.

Fóton é um agente de testes exploratórios movido por IA.
Ele lê a estrutura de uma página, entende o que pode ser feito, e age — tudo sem scripts manuais ou rotas definidas.
É como dar um mapa do seu sistema para uma inteligência que realmente caminha por ele.


---

✨ Diferenciais

Navegação dinâmica com LLMs: interpreta a página em tempo real e toma decisões.

Sem scripts fixos: você fornece uma instrução e o agente descobre os caminhos possíveis.

Compatível com LLMs locais (LM Studio, Ollama) ou OpenAI.

Playwright por trás da navegação.

Resposta em JSON estruturado + logs.



---

🧠 Exemplo de instrução

{
  "url": "https://meusistema.com/login",
  "propósito": "Testar login com credenciais inválidas",
  "estilo": "Exploratório, com foco em validação de campos e comportamento pós-erro"
}


---

🚀 Como usar

1. Clone o repositório


2. Configure o .env com sua chave OpenAI ou endpoint local


3. Execute main.py com o prompt desejado


4. O agente abrirá o navegador, tomará decisões, e responderá com logs e resultados




---

🔧 Estrutura do Projeto


📍 Roadmap (em andamento)

[ ] Visualização dos passos percorridos

[ ] Criação de um painel interativo para acompanhar a execução

[ ] Logs estruturados com score de cobertura

[ ] Modo contínuo com memória vetorial (em breve)



---

📜 Licença e apoio

Este é um projeto autoral criado por Thiago Neves, como expressão prática de uma nova forma de testar sistemas com inteligência real.
Se quiser apoiar ou contribuir, fique à vontade para entrar em contato ou abrir um pull request.


---

Se quiser, posso escrever esse README.md por completo já com seus dados e incluir sugestões de badges, estilo visual e até um pitch em vídeo/markdown. Deseja que eu gere a primeira versão agora?

