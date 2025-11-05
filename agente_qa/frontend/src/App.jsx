import { useState, useEffect, useRef } from 'react'
import { Play, Square, Trash2, Save, CheckCircle } from 'lucide-react'
import './App.css'

function App() {
  // Estados do formulário
  const [url, setUrl] = useState('https://concursos.cesgranrio.org.br/portal')
  const [maxPassos, setMaxPassos] = useState(10)
  const [modelo, setModelo] = useState('')
  const [modelos, setModelos] = useState([])
  const [loadingModels, setLoadingModels] = useState(false)
  const [instrucoes, setInstrucoes] = useState('')
  const [modoExtracao, setModoExtracao] = useState('padrao')
  const [modoTeste, setModoTeste] = useState(false)
  
  // Configuração LLM
  const [providerType, setProviderType] = useState('lmstudio_local')
  const [llmUrl, setLlmUrl] = useState('http://localhost:1234')
  const [apiKey, setApiKey] = useState('')
  
  // Estado da execução
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState([])
  
  // Refs
  const logsEndRef = useRef(null)
  
  // Configurar listeners do Electron IPC
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onPythonOutput((data) => {
        addLog(data)
      })
      
      window.electronAPI.onPythonError((error) => {
        addLog(`❌ ${error}`)
      })
    }
  }, [])
  
  // Auto-scroll dos logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])
  
  // Atualizar configuração ao mudar provider
  useEffect(() => {
    if (providerType === 'lmstudio_local') {
      setLlmUrl('http://localhost:1234')
      setApiKey('')
    } else if (providerType === 'ollama_local') {
      setLlmUrl('http://localhost:11434')
      setApiKey('')
    } else if (providerType === 'api_externa') {
      setLlmUrl('https://api.openai.com/v1')
    }
    // Limpar modelos ao trocar provider
    setModelos([])
    setModelo('')
  }, [providerType])
  
  // Buscar modelos quando URL do LLM mudar
  useEffect(() => {
    if (llmUrl && !isRunning) {
      fetchModels()
    }
  }, [llmUrl])
  
  // Atualizar campos ao ativar modo teste
  useEffect(() => {
    if (modoTeste) {
      setUrl('https://parabank.parasoft.com/parabank/index.htm')
      setMaxPassos(4)
      setInstrucoes('encontre um meio de fazer cadastro, preencha os dados necessarios com dados fake.')
    } else {
      setUrl('https://concursos.cesgranrio.org.br/portal')
      setMaxPassos(10)
      setInstrucoes('')
    }
  }, [modoTeste])
  
  const fetchModels = async () => {
    if (!window.electronAPI) {
      console.error('electronAPI não disponível')
      return
    }
    
    setLoadingModels(true)
    addLog(`🔄 Buscando modelos de ${providerType}...`)
    
    try {
      const result = await window.electronAPI.fetchModels(providerType, llmUrl)
      
      if (result.success && result.models && result.models.length > 0) {
        setModelos(result.models)
        setModelo(result.models[0]) // Selecionar primeiro modelo automaticamente
        addLog(`✅ ${result.models.length} modelo(s) encontrado(s)`)
      } else {
        addLog(`⚠️ Nenhum modelo encontrado ou erro: ${result.error || 'desconhecido'}`)
        setModelos([])
        setModelo('')
      }
    } catch (error) {
      addLog(`❌ Erro ao buscar modelos: ${error.message}`)
      setModelos([])
      setModelo('')
    } finally {
      setLoadingModels(false)
    }
  }
  
  const addLog = (message) => {
    setLogs(prev => [...prev, message])
  }
  
  const startAgent = async () => {
    if (!url) {
      alert('Por favor, insira uma URL válida')
      return
    }
    
    // Validar e corrigir URL
    let validUrl = url.trim()
    if (!validUrl.startsWith('http://') && !validUrl.startsWith('https://')) {
      validUrl = 'https://' + validUrl
      setUrl(validUrl)
    }
    
    // Construir argumentos CLI
    const args = [
      '--url', validUrl,
      '--instrucoes', instrucoes || 'Navegue pela página',
      '--max_passos', maxPassos.toString(),
      '--modelo', modelo,
      '--modo_extracao', modoExtracao
    ]
    
    // Adicionar configuração LLM se necessário
    if (providerType !== 'lmstudio_local') {
      args.push('--llm_provider', providerType)
      args.push('--llm_url', llmUrl)
      if (apiKey) {
        args.push('--llm_api_key', apiKey)
      }
    }
    
    try {
      setIsRunning(true)
      setLogs([])
      addLog('🚀 Iniciando agente...')
      addLog(`📍 URL: ${validUrl}`)
      addLog(`🤖 Modelo: ${modelo}`)
      addLog(`🔢 Max Passos: ${maxPassos}`)
      addLog('─'.repeat(50))
      
      const result = await window.electronAPI.runPythonScript('main.py', args)
      
      if (!result.success) {
        addLog(`❌ Erro: ${result.error}`)
        setIsRunning(false)
      }
    } catch (error) {
      addLog(`❌ Erro ao iniciar: ${error.message}`)
      setIsRunning(false)
    }
  }
  
  const stopAgent = async () => {
    try {
      const result = await window.electronAPI.stopPythonScript()
      if (result.success) {
        setIsRunning(false)
        addLog('⏹️ Agente parado pelo usuário')
      } else {
        addLog(`❌ Erro ao parar: ${result.error}`)
      }
    } catch (error) {
      addLog(`❌ Erro ao parar: ${error.message}`)
    }
  }
  
  const clearLogs = () => {
    setLogs([])
  }
  
  const saveConfig = () => {
    const config = {
      url,
      maxPassos,
      modelo,
      instrucoes,
      modoExtracao,
      modoTeste,
      llmConfig: { providerType, llmUrl, apiKey: apiKey ? '***' : '' }
    }
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = 'agente-config.json'
    a.click()
    URL.revokeObjectURL(downloadUrl)
    
    addLog('💾 Configuração salva')
  }
  
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>
          <span>🤖</span>
          Agente de QA Automatizado
        </h1>
        <p>Interface Desktop - Powered by Electron + React</p>
      </header>
      
      <div className="app-content">
        {/* Seção de Controles */}
        <div className="controls-section">
          {/* Configurações Básicas */}
          <div className="card">
            <h2 className="card-title">⚙️ Configurações Básicas</h2>
            
            <div className="form-group">
              <label>🔗 URL:</label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://exemplo.com"
              />
            </div>
            
            <div className="form-group">
              <label>🔢 Max Passos:</label>
              <input
                type="number"
                value={maxPassos}
                onChange={(e) => setMaxPassos(e.target.value)}
                min="1"
                max="50"
              />
            </div>
            
            <div className="form-group">
              <label>
                🤖 Modelo LLM:
                <button
                  className="btn btn-secondary"
                  onClick={fetchModels}
                  disabled={loadingModels || isRunning}
                  style={{ padding: '4px 8px', marginLeft: '10px', fontSize: '0.8rem' }}
                  title="Recarregar modelos disponíveis"
                >
                  {loadingModels ? '⏳' : '🔄'}
                </button>
              </label>
              <select 
                value={modelo} 
                onChange={(e) => setModelo(e.target.value)}
                disabled={isRunning || modelos.length === 0}
              >
                {modelos.length === 0 ? (
                  <option value="">Nenhum modelo disponível</option>
                ) : (
                  modelos.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))
                )}
              </select>
              {loadingModels && (
                <small style={{ color: '#666', marginTop: '5px', display: 'block' }}>
                  Carregando modelos...
                </small>
              )}
            </div>
            
            <div className="form-group">
              <label>⚙️ Modo de Extração:</label>
              <div className="radio-group">
                <label>
                  <input
                    type="radio"
                    value="padrao"
                    checked={modoExtracao === 'padrao'}
                    onChange={(e) => setModoExtracao(e.target.value)}
                  />
                  Padrão
                </label>
                <label>
                  <input
                    type="radio"
                    value="otimizado"
                    checked={modoExtracao === 'otimizado'}
                    onChange={(e) => setModoExtracao(e.target.value)}
                  />
                  Otimizado LLM
                </label>
              </div>
            </div>
            
            <div className="form-group">
              <div className="checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={modoTeste}
                    onChange={(e) => setModoTeste(e.target.checked)}
                  />
                  🧪 Modo Teste (ParaBank - Cadastro Automático)
                </label>
              </div>
            </div>
          </div>
          
          {/* Configuração do LLM */}
          <div className="card">
            <h2 className="card-title">🔧 Configuração do LLM</h2>
            
            <div className="form-group">
              <label>Tipo:</label>
              <select value={providerType} onChange={(e) => setProviderType(e.target.value)}>
                <option value="lmstudio_local">LM Studio Local</option>
                <option value="ollama_local">Ollama Local</option>
                <option value="api_externa">API Externa</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>URL:</label>
              <input
                type="text"
                value={llmUrl}
                onChange={(e) => setLlmUrl(e.target.value)}
              />
            </div>
            
            {providerType === 'api_externa' && (
              <div className="form-group">
                <label>🔑 API Key:</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                />
              </div>
            )}
          </div>
          
          {/* Instruções */}
          <div className="card">
            <h2 className="card-title">🎯 Instruções Customizadas</h2>
            
            <div className="form-group">
              <textarea
                value={instrucoes}
                onChange={(e) => setInstrucoes(e.target.value)}
                placeholder="Ex: Procure por editais de concursos públicos federais. Evite links de contato."
              />
            </div>
          </div>
          
          {/* Botões de Ação */}
          <div className="button-group">
            <button
              className="btn btn-primary"
              onClick={startAgent}
              disabled={isRunning}
            >
              <Play size={20} />
              Iniciar
            </button>
            <button
              className="btn btn-danger"
              onClick={stopAgent}
              disabled={!isRunning}
            >
              <Square size={20} />
              Parar
            </button>
            <button className="btn btn-secondary" onClick={clearLogs}>
              <Trash2 size={20} />
              Limpar
            </button>
            <button className="btn btn-success" onClick={saveConfig}>
              <Save size={20} />
              Salvar
            </button>
          </div>
          
          {/* Status */}
          <div className={`status-indicator ${isRunning ? 'status-running' : 'status-idle'}`}>
            {isRunning ? '▶️ Executando...' : '⏸️ Aguardando...'}
          </div>
        </div>
        
        {/* Seção de Logs */}
        <div className="logs-section">
          <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h2 className="card-title" style={{ marginBottom: 0 }}>📋 Logs em Tempo Real</h2>
              <div className="connection-status connected">
                <CheckCircle size={16} /> Electron IPC
              </div>
            </div>
            
            <div className="logs-container">
              {logs.length === 0 && (
                <div style={{ color: '#888', fontStyle: 'italic' }}>
                  Aguardando início da execução...
                </div>
              )}
              {logs.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
