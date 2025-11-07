import { useState, useEffect, useRef } from 'react'
import { Play, Square, Trash2, Save, RefreshCw, CheckCircle, XCircle, Loader } from 'lucide-react'
import './App.css'

const API_BASE = 'http://localhost:8000'

function App() {
  // Estados do formulário
  const [url, setUrl] = useState('https://concursos.cesgranrio.org.br/portal')
  const [maxPassos, setMaxPassos] = useState(10)
  const [modelo, setModelo] = useState('openai/gpt-oss-20b')
  const [modelos, setModelos] = useState([])
  const [instrucoes, setInstrucoes] = useState('')
  const [modoExtracao, setModoExtracao] = useState('padrao')
  const [modoTeste, setModoTeste] = useState(false)
  
  // Configuração LLM
  const [providerType, setProviderType] = useState('lmstudio_local')
  const [llmUrl, setLlmUrl] = useState('http://localhost:1234')
  const [apiKey, setApiKey] = useState('')
  const [connectionStatus, setConnectionStatus] = useState('idle') // idle, testing, success, error
  
  // Estado da execução
  const [isRunning, setIsRunning] = useState(false)
  const [logs, setLogs] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  
  // Refs
  const wsRef = useRef(null)
  const logsEndRef = useRef(null)
  
  // Carregar modelos ao iniciar
  useEffect(() => {
    loadModels()
  }, [])
  
  // Conectar WebSocket
  useEffect(() => {
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
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
    setConnectionStatus('idle')
  }, [providerType])
  
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
  
  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/logs')
    
    ws.onopen = () => {
      console.log('WebSocket conectado')
      setWsConnected(true)
      addLog('🟢 Conectado ao servidor de logs')
    }
    
    ws.onmessage = (event) => {
      addLog(event.data)
    }
    
    ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error)
      setWsConnected(false)
      addLog('🔴 Erro na conexão com servidor de logs')
    }
    
    ws.onclose = () => {
      console.log('WebSocket desconectado')
      setWsConnected(false)
      addLog('🔴 Desconectado do servidor de logs')
      
      // Tentar reconectar após 3 segundos
      setTimeout(connectWebSocket, 3000)
    }
    
    wsRef.current = ws
  }
  
  const addLog = (message) => {
    setLogs(prev => [...prev, message])
  }
  
  const loadModels = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/models`)
      if (response.data.success) {
        setModelos(response.data.models)
        if (response.data.loaded_model) {
          setModelo(response.data.loaded_model)
        }
      }
    } catch (error) {
      console.error('Erro ao carregar modelos:', error)
      addLog('⚠️ Erro ao carregar modelos LLM')
    }
  }
  
  const testConnection = async () => {
    setConnectionStatus('testing')
    
    try {
      const response = await axios.post(`${API_BASE}/api/llm/test`, {
        provider: providerType,
        url: llmUrl,
        api_key: apiKey
      })
      
      if (response.data.success) {
        setConnectionStatus('success')
        addLog(`✅ ${response.data.message}`)
      } else {
        setConnectionStatus('error')
        addLog(`❌ ${response.data.message}`)
      }
    } catch (error) {
      setConnectionStatus('error')
      addLog(`❌ Erro ao testar conexão: ${error.message}`)
    }
  }
  
  const startAgent = async () => {
    if (!url) {
      alert('Por favor, insira uma URL válida')
      return
    }
    
    try {
      const config = {
        url,
        max_passos: parseInt(maxPassos),
        instrucoes,
        modelo,
        modo_extracao: modoExtracao,
        llm_config: {
          provider: providerType,
          url: llmUrl,
          api_key: apiKey
        }
      }
      
      const response = await axios.post(`${API_BASE}/api/agent/start`, config)
      
      if (response.data.success) {
        setIsRunning(true)
        addLog('✅ Agente iniciado com sucesso')
      }
    } catch (error) {
      console.error('Erro ao iniciar agente:', error)
      addLog(`❌ Erro ao iniciar: ${error.response?.data?.detail || error.message}`)
    }
  }
  
  const stopAgent = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/agent/stop`)
      
      if (response.data.success) {
        setIsRunning(false)
        addLog('⏹️ Agente parado')
      }
    } catch (error) {
      console.error('Erro ao parar agente:', error)
      addLog(`❌ Erro ao parar: ${error.response?.data?.detail || error.message}`)
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
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'agente-config.json'
    a.click()
    URL.revokeObjectURL(url)
    
    addLog('💾 Configuração salva')
  }
  
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>
          <span>🤖</span>
          Agente de QA Automatizado
        </h1>
        <p>Interface Web Moderna - Powered by React + FastAPI</p>
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
                  onClick={loadModels}
                  style={{ padding: '4px 8px', marginLeft: '10px', fontSize: '0.8rem' }}
                >
                  <RefreshCw size={14} />
                </button>
              </label>
              <select value={modelo} onChange={(e) => setModelo(e.target.value)}>
                {modelos.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
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
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className={`connection-status ${connectionStatus === 'success' ? 'connected' : connectionStatus === 'error' ? 'disconnected' : connectionStatus === 'testing' ? 'testing' : ''}`}>
                {connectionStatus === 'idle' && '⚪ Não testado'}
                {connectionStatus === 'testing' && <><Loader size={16} /> Testando...</>}
                {connectionStatus === 'success' && <><CheckCircle size={16} /> Conectado</>}
                {connectionStatus === 'error' && <><XCircle size={16} /> Erro</>}
              </div>
              <button className="btn btn-secondary" onClick={testConnection}>
                🧪 Testar Conexão
              </button>
            </div>
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
              <div className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
                {wsConnected ? <><CheckCircle size={16} /> Conectado</> : <><XCircle size={16} /> Desconectado</>}
              </div>
            </div>
            
            <div className="logs-container">
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
