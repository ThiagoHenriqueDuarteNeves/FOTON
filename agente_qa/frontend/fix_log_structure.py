# -*- coding: utf-8 -*-
import re

# Ler arquivo
with open('src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar e substituir a função renderStep completa
old_pattern = r'  // Renderização formatada e legível\s+const renderStep = \(step, idx\) => \{.*?// Se for type=output, mostra RESPOSTA do LLM'

new_code = '''  // Renderização formatada e legível
  const renderStep = (step, idx) => {
    let data = step;
    if (typeof step === 'string') {
      try { data = JSON.parse(step); } catch (e) { return null; }
    }
    
    // Nova estrutura: data agora tem { response, payload, responsePath, payloadPath }
    const response = data.response || data; // Fallback para estrutura antiga
    const payload = data.payload || null;
    
    // Extrair informações da resposta (SAÍDA do LLM)
    const passo = response.passo !== undefined ? response.passo : idx;
    const acaoParseada = response.acao_parseada || {};
    const acao = acaoParseada.action || response.acao || '-';
    const seletor = acaoParseada.selector || response.seletor || '-';
    const valor = acaoParseada.value || response.valor || '';
    const confianca = acaoParseada.confidence || response.confianca || 0;
    const justificativa = acaoParseada.justification || response.justificativa || 'Não fornecida';
    const timestamp = response.timestamp || '';
    const modelo = response.modelo || '';
    const respostaBruta = response.resposta_bruta || '';
    const metadados = response.metadados || {};
    
    // Se for type=input, mostra dados ENVIADOS ao LLM (PAYLOAD)
    if (type === 'input') {
      if (!payload) {
        return (
          <div key={idx} style={{ 
            marginBottom: '20px', 
            background: '#1a1f2e', 
            borderRadius: '8px', 
            padding: '20px',
            border: '1px solid #2a3f5f'
          }}>
            <div style={{ color: '#999', fontStyle: 'italic', textAlign: 'center' }}>
              📭 Payload não disponível para este passo
            </div>
          </div>
        );
      }
      
      // Extrair mensagens do payload
      const messages = payload.messages || [];
      const systemMessage = messages.find(m => m.role === 'system')?.content || '';
      const userMessage = messages.find(m => m.role === 'user')?.content || '';
      
      return (
        <div key={idx} style={{ 
          marginBottom: '20px', 
          background: '#1a1f2e', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #2a3f5f'
        }}>
          <div style={{ 
            fontSize: '18px', 
            fontWeight: 'bold', 
            color: '#4fc3f7', 
            marginBottom: '15px',
            borderBottom: '2px solid #2a3f5f',
            paddingBottom: '10px'
          }}>
            📤 PASSO {passo} - Dados Enviados ao LLM
          </div>
          
          <div style={{ marginBottom: '12px', color: '#e0e0e0', fontSize: '14px' }}>
            <span style={{ color: '#81c784', fontWeight: 600 }}>🤖 Modelo:</span>{' '}
            {payload.model || modelo}
          </div>
          
          <div style={{ marginBottom: '12px', color: '#e0e0e0', fontSize: '14px' }}>
            <span style={{ color: '#ffa726', fontWeight: 600 }}>🌡️ Temperature:</span>{' '}
            {payload.temperature !== undefined ? payload.temperature : 'N/A'}
          </div>
          
          <div style={{ marginBottom: '12px', color: '#e0e0e0', fontSize: '14px' }}>
            <span style={{ color: '#ab47bc', fontWeight: 600 }}>🔢 Max Tokens:</span>{' '}
            {payload.max_tokens || 'N/A'}
          </div>
          
          {systemMessage && (
            <div style={{ marginTop: '15px' }}>
              <div style={{ color: '#4fc3f7', fontWeight: 600, marginBottom: '8px', fontSize: '14px' }}>
                ⚙️ System Prompt:
              </div>
              <div style={{ 
                background: '#0d1117', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '12px',
                color: '#c9d1d9',
                maxHeight: '200px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: '1.5'
              }}>
                {systemMessage.substring(0, 500)}
                {systemMessage.length > 500 && (
                  <details style={{ marginTop: '8px' }}>
                    <summary style={{ cursor: 'pointer', color: '#81c784' }}>
                      ... Ver mais ({systemMessage.length - 500} caracteres)
                    </summary>
                    <div style={{ marginTop: '8px' }}>
                      {systemMessage.substring(500)}
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}
          
          {userMessage && (
            <div style={{ marginTop: '15px' }}>
              <div style={{ color: '#ffeb3b', fontWeight: 600, marginBottom: '8px', fontSize: '14px' }}>
                👤 User Message:
              </div>
              <div style={{ 
                background: '#0d1117', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '12px',
                color: '#c9d1d9',
                maxHeight: '200px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: '1.5'
              }}>
                {userMessage.substring(0, 500)}
                {userMessage.length > 500 && (
                  <details style={{ marginTop: '8px' }}>
                    <summary style={{ cursor: 'pointer', color: '#81c784' }}>
                      ... Ver mais ({userMessage.length - 500} caracteres)
                    </summary>
                    <div style={{ marginTop: '8px' }}>
                      {userMessage.substring(500)}
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}
        </div>
      );
    }
    
    // Se for type=output, mostra RESPOSTA do LLM'''

# Substituir usando regex com DOTALL flag
content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

# Salvar
with open('src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Estrutura de logs atualizada com sucesso!")
print("  → Agora trabalha com payload (entrada) e response (saída) separadamente")
print("  → Coluna ESQUERDA: Mostra payload com system/user messages")
print("  → Coluna DIREITA: Mantém resposta do LLM")
