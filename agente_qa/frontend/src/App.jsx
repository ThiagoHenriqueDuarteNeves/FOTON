import React, { useState, useEffect, useRef } from 'react';
// Componente para exibição dos passos (SEM navegação interna)
function LogStepsViewer({ logs, type }) {
  // Filtra logs válidos (JSON)
  const validLogs = logs.filter(log => {
    if (typeof log === 'object') return true;
    try {
      JSON.parse(log);
      return true;
    } catch (e) {
      return false;
    }
  });
  
  // Pega apenas o primeiro log (navegação é feita externamente)
  const currentStep = validLogs[0];
  
  // Renderização formatada e legível
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
    
    // Se for type=output, mostra RESPOSTA do LLM
    if (type === 'output') {
      return (
        <div key={idx} style={{ 
          marginBottom: '20px', 
          background: '#1e2a1a', 
          borderRadius: '8px', 
          padding: '20px',
          border: '1px solid #3a5f2a'
        }}>
          <div style={{ 
            fontSize: '18px', 
            fontWeight: 'bold', 
            color: '#81c784', 
            marginBottom: '15px',
            borderBottom: '2px solid #3a5f2a',
            paddingBottom: '10px'
          }}>
            � PASSO {passo} - Decisão do LLM
          </div>
          
          <div style={{ 
            background: '#0f1610', 
            padding: '16px', 
            borderRadius: '6px',
            marginBottom: '15px',
            border: '1px solid #2a4a1a'
          }}>
            <div style={{ fontSize: '15px', marginBottom: '10px' }}>
              <span style={{ color: '#90caf9', fontWeight: 600 }}>Ação:</span>{' '}
              <span style={{ 
                color: '#fff', 
                background: acao === 'click' ? '#1976d2' : acao === 'type' ? '#388e3c' : '#f57c00',
                padding: '4px 10px',
                borderRadius: '4px',
                fontWeight: 600,
                textTransform: 'uppercase',
                fontSize: '13px'
              }}>
                {acao}
              </span>
            </div>
            
            <div style={{ fontSize: '14px', marginBottom: '10px', color: '#e0e0e0' }}>
              <span style={{ color: '#ce93d8', fontWeight: 600 }}>Seletor:</span>{' '}
              <code style={{ 
                background: '#000', 
                padding: '4px 8px', 
                borderRadius: '4px',
                color: '#4fc3f7',
                fontSize: '13px'
              }}>
                {seletor}
              </code>
            </div>
            
            {valor && (
              <div style={{ fontSize: '14px', marginBottom: '10px', color: '#e0e0e0' }}>
                <span style={{ color: '#ffb74d', fontWeight: 600 }}>Valor:</span>{' '}
                <span style={{ color: '#fff', fontStyle: 'italic' }}>"{valor}"</span>
              </div>
            )}
            
            <div style={{ fontSize: '14px', marginBottom: '0', color: '#e0e0e0' }}>
              <span style={{ color: '#a5d6a7', fontWeight: 600 }}>Confiança:</span>{' '}
              <span style={{ 
                color: confianca >= 90 ? '#4caf50' : confianca >= 70 ? '#ff9800' : '#f44336',
                fontWeight: 700,
                fontSize: '15px'
              }}>
                {confianca}%
              </span>
            </div>
          </div>
          
          {justificativa && justificativa !== 'Não fornecida' && (
            <div style={{ marginBottom: '15px' }}>
              <div style={{ color: '#ffeb3b', fontWeight: 600, marginBottom: '8px', fontSize: '14px' }}>
                💡 Justificativa:
              </div>
              <div style={{ 
                background: '#0f1610', 
                padding: '12px', 
                borderRadius: '6px',
                fontSize: '13px',
                color: '#e0e0e0',
                lineHeight: '1.6',
                fontStyle: 'italic',
                border: '1px solid #2a4a1a'
              }}>
                "{justificativa}"
              </div>
            </div>
          )}
          
          {respostaBruta && (
            <div>
              <details>
                <summary style={{ 
                  color: '#999', 
                  cursor: 'pointer', 
                  fontSize: '12px',
                  marginBottom: '8px'
                }}>
                  🔍 Ver resposta bruta do LLM
                </summary>
                <div style={{ 
                  background: '#0d1117', 
                  padding: '10px', 
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#8b949e',
                  maxHeight: '150px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {respostaBruta}
                </div>
              </details>
            </div>
          )}
        </div>
      );
    }
    
    return null;
  };
  
  return (
    <div>
      {currentStep ? (
        renderStep(currentStep, 0)
      ) : (
        <div style={{ 
          color: '#999', 
          fontStyle: 'italic', 
          textAlign: 'center',
          padding: '40px 20px',
          background: '#2a2a2a',
          borderRadius: '8px',
          border: '1px dashed #444'
        }}>
          ❌ Nenhum dado disponível para exibir
        </div>
      )}
    </div>
  );
}
import { Play, Square, Trash2, Save, CheckCircle } from 'lucide-react'
import './App.css'

function App() {
  // ...existing states...
  const [url, setUrl] = useState('https://concursos.cesgranrio.org.br/portal');
  const [maxPassos, setMaxPassos] = useState(10);
  const [modelo, setModelo] = useState('');
  const [modelos, setModelos] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [instrucoes, setInstrucoes] = useState('');
  const [modoExtracao, setModoExtracao] = useState('padrao');
  const [modoTeste, setModoTeste] = useState(false);
  const [providerType, setProviderType] = useState('lmstudio_local');
  const [llmUrl, setLlmUrl] = useState('http://localhost:1234');
  const [apiKey, setApiKey] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);
  const [stepFilesList, setStepFilesList] = useState([]);
  const [selectedStepPath, setSelectedStepPath] = useState('');
  const [loadingStepFiles, setLoadingStepFiles] = useState(false);
  const [currentStepData, setCurrentStepData] = useState(null);
  const [moreStepsCount, setMoreStepsCount] = useState(0);
  const [allStepsData, setAllStepsData] = useState([]); // NOVO: armazena todos os steps carregados
  const [currentStepIndex, setCurrentStepIndex] = useState(0); // NOVO: índice do step atual
  const [executedStepsCount, setExecutedStepsCount] = useState(0); // NOVO: contador de passos da execução atual
  const [initialStepsCount, setInitialStepsCount] = useState(0); // NOVO: quantidade de passos antes de iniciar
  
  // Estados para seleção de pasta customizada
  const [selectedRootFolder, setSelectedRootFolder] = useState(null);
  const [availableFolders, setAvailableFolders] = useState([]);
  const [expandedFolderSelector, setExpandedFolderSelector] = useState(false);
  const [selectedLogFolder, setSelectedLogFolder] = useState(null);
  
  // Estados para controle de expansão de seções
  const [logsExpanded, setLogsExpanded] = useState(false);
  const [configExpanded, setConfigExpanded] = useState(false);
  const [isSmallScreen, setIsSmallScreen] = useState(window.innerWidth < 1024);

  // Listener para detectar mudanças no tamanho da janela
  useEffect(() => {
    const handleResize = () => {
      setIsSmallScreen(window.innerWidth < 1024);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Novo: listar arquivos de passos e carregar TODOS automaticamente
  useEffect(() => {
    async function listAndLoadFiles() {
      if (!window.electronAPI || !window.electronAPI.listStepLogs) return;
      setLoadingStepFiles(true);
      try {
        const res = await window.electronAPI.listStepLogs();
        if (res && res.success && Array.isArray(res.files)) {
          setStepFilesList(res.files);
          
          // Carregar TODOS os passos de uma vez
          if (res.files.length > 0) {
            console.log(`Carregando ${res.files.length} arquivos de log...`);
            const allPaths = res.files.map(f => f.path);
            
            try {
              const loaded = await window.electronAPI.fetchStepLogs(allPaths);
              if (Array.isArray(loaded)) {
                setAllStepsData(loaded);
                setCurrentStepIndex(0); // Começa no primeiro (mais recente)
                setCurrentStepData(loaded[0]); // Define o primeiro como atual
                setMoreStepsCount(Math.max(0, loaded.length - 1));
                console.log(`✓ ${loaded.length} passos carregados com sucesso`);
              }
            } catch (e) {
              console.error('Erro ao carregar todos os passos:', e);
            }
          }
        } else {
          setStepFilesList([]);
          setAllStepsData([]);
        }
      } catch (e) {
        console.error('Erro ao listar arquivos de passos:', e);
        setStepFilesList([]);
        setAllStepsData([]);
      } finally {
        setLoadingStepFiles(false);
      }
    }
    listAndLoadFiles();
  }, []);

  // Listener para detectar novos arquivos de log em tempo real
  useEffect(() => {
    if (!window.electronAPI?.onStepLogChanged) return;
    
    const handleLogChange = async (data) => {
      console.log('📁 Novo arquivo de log detectado:', data);
      // Recarregar lista de arquivos automaticamente
      try {
        const res = await window.electronAPI.listStepLogs();
        if (res && res.success && Array.isArray(res.files)) {
          setStepFilesList(res.files);
          console.log(`✓ Lista atualizada: ${res.files.length} arquivos`);
        }
      } catch (e) {
        console.error('Erro ao atualizar lista após mudança:', e);
      }
    };
    
    window.electronAPI.onStepLogChanged(handleLogChange);
    
    // Cleanup não é necessário pois ipcRenderer.on não retorna unsubscribe
  }, []);

  const handleRefreshStepFiles = async () => {
    if (!window.electronAPI || !window.electronAPI.listStepLogs) return;
    setLoadingStepFiles(true);
    try {
      const res = await window.electronAPI.listStepLogs();
      if (res && res.success && res.files) {
        setStepFilesList(res.files);
        
        // Recarregar todos os passos
        if (res.files.length > 0) {
          const allPaths = res.files.map(f => f.path);
          const loaded = await window.electronAPI.fetchStepLogs(allPaths);
          if (Array.isArray(loaded)) {
            setAllStepsData(loaded);
            setCurrentStepIndex(0);
            setCurrentStepData(loaded[0]);
            setMoreStepsCount(Math.max(0, loaded.length - 1));
          }
        }
      }
    } catch (e) {
      console.error('Erro ao atualizar:', e);
    } finally {
      setLoadingStepFiles(false);
    }
  }
  
  // NOVA FUNÇÃO: Navegar entre os passos
  const handleNavigateStep = (direction) => {
    const newIndex = direction === 'next' 
      ? Math.min(allStepsData.length - 1, currentStepIndex + 1)
      : Math.max(0, currentStepIndex - 1);
    
    setCurrentStepIndex(newIndex);
    setCurrentStepData(allStepsData[newIndex]);
  };
  
  // Funções para expandir/recolher seções
  const toggleLogsExpanded = () => {
    if (!logsExpanded) {
      setConfigExpanded(false); // Fecha a outra seção
    }
    setLogsExpanded(!logsExpanded);
  };
  
  const toggleConfigExpanded = () => {
    if (!configExpanded) {
      setLogsExpanded(false); // Fecha a outra seção
    }
    setConfigExpanded(!configExpanded);
  };

  const handleLoadSelectedStep = async () => {
    if (!selectedStepPath) return;
    if (!window.electronAPI || !window.electronAPI.fetchStepLogs) return;
    try {
      const loaded = await window.electronAPI.fetchStepLogs([selectedStepPath]);
      // fetchStepLogs retorna array com JSONs lidos
      if (Array.isArray(loaded)) setLogs(loaded);
      else setLogs([loaded]);
    } catch (e) {
      console.error('Erro ao carregar passo:', e);
      addLog(`❌ Erro ao carregar passo: ${e.message}`);
    }
  }
  
  // Funções para seleção de pasta customizada
  const handleSelectRootFolder = async () => {
    if (!window.electronAPI?.selectLogsFolder) return;
    try {
      const result = await window.electronAPI.selectLogsFolder();
      if (result.success && result.path) {
        setSelectedRootFolder(result.path);
        // Varrer subpastas
        const scanResult = await window.electronAPI.scanLogsFolder(result.path);
        if (scanResult.success && scanResult.folders) {
          setAvailableFolders(scanResult.folders);
          setExpandedFolderSelector(true);
        }
      }
    } catch (e) {
      console.error('Erro ao selecionar pasta:', e);
    }
  };
  
  const handleSelectLogFolder = async (folder) => {
    setSelectedLogFolder(folder);
    setExpandedFolderSelector(false);
    
    // Carregar logs desta pasta
    if (!window.electronAPI?.listStepLogsFromFolder) return;
    setLoadingStepFiles(true);
    try {
      const res = await window.electronAPI.listStepLogsFromFolder(folder.path);
      if (res && res.success && Array.isArray(res.files)) {
        setStepFilesList(res.files);
        if (res.files.length > 0) {
          const first = res.files[0];
          setSelectedStepPath(first.path);
          setMoreStepsCount(Math.max(0, res.files.length - 1));
          // Carregar primeiro passo
          const loaded = await window.electronAPI.fetchStepLogs([first.path]);
          if (Array.isArray(loaded) && loaded.length > 0) setCurrentStepData(loaded[0]);
        }
      }
    } catch (e) {
      console.error('Erro ao carregar logs da pasta:', e);
    } finally {
      setLoadingStepFiles(false);
    }
  };
  
  // Monitorar novos passos durante execução
  useEffect(() => {
    if (isRunning) {
      // Durante a execução, conta apenas os arquivos NOVOS (criados após o início)
      const newStepsCount = Math.max(0, stepFilesList.length - initialStepsCount);
      setExecutedStepsCount(newStepsCount);
    }
  }, [stepFilesList.length, isRunning, initialStepsCount]);
  
  // NOTE: removemos o listener que encaminhava stdout/stderr do Python
  // para o frontend para evitar logs verborrágicos na UI. O output
  // do Python continua sendo impresso no console do Electron.
  
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
      setInitialStepsCount(stepFilesList.length) // Salva quantos arquivos existem antes de iniciar
      setExecutedStepsCount(0) // Reseta o contador de passos executados
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
        setExecutedStepsCount(0) // Reseta o contador ao parar
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
        <div 
          className="controls-section" 
          style={{ 
            display: logsExpanded ? 'none' : 'block',
            transition: 'all 0.3s ease',
            ...(configExpanded ? {
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              margin: 0,
              borderRadius: 0,
              zIndex: 1000,
              height: '100vh',
              overflowY: 'auto',
              background: '#1a1a2e',
              padding: '20px'
            } : {})
          }}
        >
          {/* Botão para expandir configurações */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end', 
            marginBottom: '15px' 
          }}>
            <button
              className="btn btn-secondary"
              onClick={toggleConfigExpanded}
              style={{ 
                padding: '8px 16px', 
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {configExpanded ? '📉 Recolher' : '📈 Expandir'} Configurações
            </button>
          </div>
          
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
          
          {/* Barra de Progresso */}
          <div style={{ marginTop: '20px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '8px'
            }}>
              <span style={{ 
                fontSize: '14px', 
                fontWeight: 600,
                color: isRunning ? '#4CAF50' : '#999'
              }}>
                {isRunning ? '▶️ Executando' : '⏸️ Aguardando'}
              </span>
              <span style={{ 
                fontSize: '13px', 
                color: '#ddd',
                fontWeight: 500
              }}>
                {isRunning ? `${executedStepsCount} / ${maxPassos} passos` : `0 / ${maxPassos} passos`}
              </span>
            </div>
            
            {/* Barra de progresso visual */}
            <div style={{
              width: '100%',
              height: '24px',
              backgroundColor: '#2a2a3e',
              borderRadius: '12px',
              overflow: 'hidden',
              border: '1px solid #3a3a5e',
              position: 'relative'
            }}>
              {/* Fundo da barra com segmentos */}
              <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                display: 'flex'
              }}>
                {[...Array(maxPassos)].map((_, i) => (
                  <div key={i} style={{
                    flex: 1,
                    borderRight: i < maxPassos - 1 ? '1px solid #3a3a5e' : 'none'
                  }} />
                ))}
              </div>
              
              {/* Barra de progresso preenchida */}
              <div style={{
                width: isRunning ? `${(Math.min(executedStepsCount, maxPassos) / maxPassos) * 100}%` : '0%',
                height: '100%',
                background: isRunning 
                  ? 'linear-gradient(90deg, #4CAF50, #66BB6A)' 
                  : 'linear-gradient(90deg, #2196F3, #42A5F5)',
                transition: 'width 0.5s ease',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                paddingRight: '8px'
              }}>
                {isRunning && executedStepsCount > 0 && (
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#fff',
                    textShadow: '0 1px 2px rgba(0,0,0,0.3)'
                  }}>
                    {Math.round((Math.min(executedStepsCount, maxPassos) / maxPassos) * 100)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Seção de Logs: duas colunas lado a lado (input | output) */}
        <div 
          className="card" 
          style={{ 
            marginTop: '20px',
            display: configExpanded ? 'none' : 'block',
            ...(logsExpanded ? {
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              margin: 0,
              borderRadius: 0,
              zIndex: 1000,
              height: '100vh',
              overflowY: 'auto'
            } : {})
          }}
        >
          {/* Cabeçalho com info do passo e botões */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 className="card-title" style={{ marginBottom: 0, color: '#fff' }}>📋 Logs do Passo</h2>
              {selectedStepPath && (
                <>
                  <span style={{ color: '#ddd', fontSize: '14px', fontWeight: 500 }}>
                    {stepFilesList.find(s => s.path === selectedStepPath)?.name || 'Passo selecionado'}
                  </span>
                  {moreStepsCount > 0 && (
                    <span style={{ fontSize: '12px', color: '#999', background: '#333', padding: '2px 8px', borderRadius: '10px' }}>+{moreStepsCount} mais</span>
                  )}
                </>
              )}
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className="btn btn-secondary"
                onClick={toggleLogsExpanded}
                style={{ 
                  padding: '8px 16px', 
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                {logsExpanded ? '📉 Recolher' : '📈 Expandir'} Logs
              </button>
              <button className="btn btn-secondary" onClick={handleRefreshStepFiles} disabled={loadingStepFiles}>
                {loadingStepFiles ? '🔄 Atualizando...' : '🔄 Atualizar'}
              </button>
            </div>
          </div>

          {/* Seletor de Pasta Customizada */}
          <div style={{ marginBottom: '20px', padding: '15px', background: '#2a2a2a', borderRadius: '8px', border: '1px solid #444' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <button 
                className="btn btn-primary" 
                onClick={handleSelectRootFolder}
                style={{ fontSize: '13px', padding: '8px 16px' }}
              >
                📁 Selecionar Pasta de Logs
              </button>
              {selectedRootFolder && (
                <span style={{ color: '#81c784', fontSize: '13px' }}>
                  📂 {selectedRootFolder.split('\\').pop() || selectedRootFolder}
                </span>
              )}
              {selectedLogFolder && (
                <span style={{ color: '#4fc3f7', fontSize: '13px', fontWeight: 600 }}>
                  → Usando: {selectedLogFolder.name} ({selectedLogFolder.fileCount} arquivos)
                </span>
              )}
            </div>
            
            {/* Lista expansível de subpastas */}
            {availableFolders.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <button
                  onClick={() => setExpandedFolderSelector(!expandedFolderSelector)}
                  style={{
                    background: '#333',
                    color: '#ddd',
                    border: '1px solid #555',
                    padding: '6px 12px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    width: '100%',
                    textAlign: 'left',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span>
                    {expandedFolderSelector ? '▼' : '▶'} {availableFolders.length} subpasta(s) disponível(is)
                  </span>
                </button>
                
                {expandedFolderSelector && (
                  <div style={{ 
                    marginTop: '8px', 
                    maxHeight: '200px', 
                    overflowY: 'auto',
                    background: '#1a1a1a',
                    borderRadius: '4px',
                    border: '1px solid #333'
                  }}>
                    {availableFolders.map((folder, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleSelectLogFolder(folder)}
                        style={{
                          padding: '10px 12px',
                          borderBottom: idx < availableFolders.length - 1 ? '1px solid #333' : 'none',
                          cursor: 'pointer',
                          background: selectedLogFolder?.path === folder.path ? '#2a4a2a' : 'transparent',
                          transition: 'background 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          if (selectedLogFolder?.path !== folder.path) {
                            e.currentTarget.style.background = '#333';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (selectedLogFolder?.path !== folder.path) {
                            e.currentTarget.style.background = 'transparent';
                          }
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ 
                            color: selectedLogFolder?.path === folder.path ? '#81c784' : '#ddd',
                            fontSize: '13px',
                            fontWeight: selectedLogFolder?.path === folder.path ? 600 : 400
                          }}>
                            📂 {folder.name}
                          </span>
                          <span style={{ 
                            color: '#999', 
                            fontSize: '11px',
                            background: '#222',
                            padding: '2px 6px',
                            borderRadius: '3px'
                          }}>
                            {folder.fileCount} arquivo{folder.fileCount !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Debug: mostrar status */}
          {!currentStepData && stepFilesList.length > 0 && (
            <div style={{ padding: '10px', background: '#2a2a2a', borderRadius: '6px', marginBottom: '10px', color: '#ff9800' }}>
              ⚠️ {stepFilesList.length} arquivo(s) encontrado(s), mas dados não carregados. Clique em Atualizar.
            </div>
          )}

          {/* Navegação entre passos */}
          {allStepsData.length > 0 && (
            <div style={{ 
              display: 'flex', 
              gap: '10px', 
              marginBottom: '20px', 
              justifyContent: 'center',
              alignItems: 'center',
              padding: '15px',
              background: '#2a2a2a',
              borderRadius: '8px',
              border: '1px solid #444'
            }}>
              <button 
                className="btn btn-secondary" 
                style={{ minWidth: 100, fontSize: '14px', padding: '10px 20px' }} 
                onClick={() => handleNavigateStep('prev')} 
                disabled={currentStepIndex === 0}
              >
                ⬅️ Anterior
              </button>
              <div style={{ 
                color: '#fff', 
                fontSize: '16px', 
                fontWeight: 700,
                padding: '10px 20px',
                background: '#1a1a1a',
                borderRadius: '6px',
                border: '2px solid #4fc3f7',
                minWidth: '150px',
                textAlign: 'center'
              }}>
                Passo {currentStepIndex + 1} de {allStepsData.length}
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ minWidth: 100, fontSize: '14px', padding: '10px 20px' }} 
                onClick={() => handleNavigateStep('next')} 
                disabled={currentStepIndex >= allStepsData.length - 1}
              >
                Próximo ➡️
              </button>
            </div>
          )}

          {/* Duas colunas: input | output - Responsivo */}
          <div style={{ 
            display: 'grid',
            gridTemplateColumns: isSmallScreen ? '1fr' : '1fr 1fr',
            gap: '20px', 
            minHeight: '400px'
          }}>
            {/* Coluna Esquerda: Dados enviados ao LLM */}
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <h3 style={{ color: '#4fc3f7', marginTop: 0, marginBottom: '12px', fontSize: '18px', fontWeight: 600 }}>
                📊 Dados enviados ao LLM
              </h3>
              <div style={{ 
                flex: 1,
                minHeight: '300px', 
                maxHeight: '700px', 
                overflowY: 'auto', 
                overflowX: 'auto',
                padding: '15px', 
                background: '#1a1a1a', 
                borderRadius: '8px',
                border: '1px solid #333'
              }}>
                {currentStepData ? (
                  <LogStepsViewer logs={[currentStepData]} type="input" />
                ) : (
                  <div style={{ color: '#999', fontStyle: 'italic', padding: '20px', textAlign: 'center' }}>
                    {stepFilesList.length === 0 ? '📭 Nenhum arquivo de log encontrado' : '⏳ Aguardando carregamento...'}
                  </div>
                )}
              </div>
            </div>

            {/* Coluna Direita: Resposta do LLM */}
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
              <h3 style={{ color: '#81c784', marginTop: 0, marginBottom: '12px', fontSize: '18px', fontWeight: 600 }}>
                💡 Resposta do LLM
              </h3>
              <div style={{ 
                flex: 1,
                minHeight: '300px', 
                maxHeight: '700px', 
                overflowY: 'auto',
                overflowX: 'auto',
                padding: '15px', 
                background: '#1a1a1a', 
                borderRadius: '8px',
                border: '1px solid #333'
              }}>
                {currentStepData ? (
                  <LogStepsViewer logs={[currentStepData]} type="output" />
                ) : (
                  <div style={{ color: '#999', fontStyle: 'italic', padding: '20px', textAlign: 'center' }}>
                    {stepFilesList.length === 0 ? '📭 Nenhum arquivo de log encontrado' : '⏳ Aguardando carregamento...'}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
// ...existing code...
      </div>
    </div>
  )
}

export default App
