#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ler o arquivo App.jsx
with open('App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar a seção de logs problemática usando regex mais robusto
# A seção vai de "Seção de Logs" até antes do próximo comentário ou fim da estrutura

# Vamos fazer algo mais simples: localizar pelo comentário e substituir manualmente
# até o fechamento correto observado visualmente (linha 556 aproximadamente)

lines = content.split('\n')

# Encontrar início (linha 501 aproximadamente - comentário "Seção de Logs")
start_idx = None
for i, line in enumerate(lines):
    if 'Seção de Logs' in line and 'duas colunas' in line:
        start_idx = i
        break

if start_idx is None:
    print("❌ Não encontrei a seção de logs")
    exit(1)

# Procurar fechamento - linha 556 é "// ...existing code..." então vamos até antes
# Procuramos por "// ...existing code..." ou fim do arquivo
end_idx = None
for i in range(start_idx + 1, len(lines)):
    if '// ...existing code...' in lines[i] or lines[i].strip() == '</div>':
        # Verificar se é um fechamento de alto nível (poucas indentações)
        spaces = len(lines[i]) - len(lines[i].lstrip())
        if spaces <= 8:  # poucas indentações = nível alto
            end_idx = i - 1  # pegar até a linha anterior
            break

if end_idx is None:
    # Fallback: pegar até 60 linhas depois
    end_idx = min(start_idx + 60, len(lines) - 1)

print(f"📍 Encontrei seção de logs: linhas {start_idx+1} a {end_idx+1}")

# Criar o novo conteúdo
new_section = '''        {/* Seção de Logs: duas colunas lado a lado (input | output) */}
        <div className="card" style={{ marginTop: '20px' }}>
          {/* Cabeçalho com info do passo e botão de atualizar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="card-title" style={{ marginBottom: 0 }}>📋 Logs do Passo</h2>
              {selectedStepPath && (
                <>
                  <span style={{ color: '#aaa', fontSize: '14px' }}>
                    {stepFilesList.find(s => s.path === selectedStepPath)?.name || 'Passo selecionado'}
                  </span>
                  {moreStepsCount > 0 && (
                    <span style={{ fontSize: '12px', color: '#888' }}>+{moreStepsCount} mais</span>
                  )}
                </>
              )}
            </div>
            <button className="btn btn-secondary" onClick={handleRefreshStepFiles} disabled={loadingStepFiles}>
              {loadingStepFiles ? '🔄 Atualizando...' : '🔄 Atualizar'}
            </button>
          </div>

          {/* Duas colunas: input | output */}
          <div style={{ display: 'flex', gap: '20px' }}>
            {/* Coluna Esquerda: Dados enviados ao LLM */}
            <div style={{ flex: 1 }}>
              <h3 style={{ color: '#8be9fd', marginTop: 0 }}>📊 Dados enviados ao LLM</h3>
              <div style={{ minHeight: '350px', maxHeight: '500px', overflowY: 'auto', padding: '10px', background: '#1e1e1e', borderRadius: '6px' }}>
                {currentStepData ? (
                  <LogStepsViewer logs={[currentStepData]} type="input" />
                ) : (
                  <div style={{ color: '#888', fontStyle: 'italic' }}>
                    Aguardando primeiro passo...
                  </div>
                )}
              </div>
            </div>

            {/* Coluna Direita: Resposta do LLM */}
            <div style={{ flex: 1 }}>
              <h3 style={{ color: '#50fa7b', marginTop: 0 }}>💡 Resposta do LLM</h3>
              <div style={{ minHeight: '350px', maxHeight: '500px', overflowY: 'auto', padding: '10px', background: '#1e1e1e', borderRadius: '6px' }}>
                {currentStepData ? (
                  <LogStepsViewer logs={[currentStepData]} type="output" />
                ) : (
                  <div style={{ color: '#888', fontStyle: 'italic' }}>
                    Aguardando primeiro passo...
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>'''

# Reconstruir o arquivo
new_lines = lines[:start_idx] + [new_section] + lines[end_idx+1:]
new_content = '\n'.join(new_lines)

# Salvar
with open('App.jsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Correção aplicada! Substituídas linhas {start_idx+1} a {end_idx+1}")
