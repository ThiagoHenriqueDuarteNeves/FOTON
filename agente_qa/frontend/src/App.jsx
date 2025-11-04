import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [maxSteps, setMaxSteps] = useState(10);
  const [customInstructions, setCustomInstructions] = useState('');
  const [modelo, setModelo] = useState('');
  const [modoExtracao, setModoExtracao] = useState('padrao');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.onPythonOutput((data) => {
        setLogs(prev => [...prev, { type: 'output', text: data }]);
      });
      window.electronAPI.onPythonError((data) => {
        setLogs(prev => [...prev, { type: 'error', text: data }]);
      });
    }
  }, []);

  const handleStart = async () => {
    if (!url) {
      alert('Por favor, insira uma URL');
      return;
    }
    if (!customInstructions) {
      alert('Por favor, insira instruções para o agente');
      return;
    }
    
    // Validar e corrigir URL se necessário
    let validUrl = url.trim();
    if (!validUrl.startsWith('http://') && !validUrl.startsWith('https://')) {
      validUrl = 'https://' + validUrl;
      setUrl(validUrl); // Atualizar o campo com a URL corrigida
    }
    
    setIsRunning(true);
    setLogs([{ type: 'info', text: '🚀 Iniciando agente...' }]);
    try {
      // Passar argumentos no formato CLI esperado pelo Python
      const args = [
        '--url', validUrl,
        '--instrucoes', customInstructions,
        '--max_passos', maxSteps.toString()
      ];
      
      // Adicionar argumentos opcionais se fornecidos
      if (modelo) {
        args.push('--modelo', modelo);
      }
      if (modoExtracao) {
        args.push('--modo_extracao', modoExtracao);
      }
      
      await window.electronAPI.runPythonScript('main.py', args);
      setLogs(prev => [...prev, { type: 'success', text: '✅ Concluído!' }]);
    } catch (error) {
      setLogs(prev => [...prev, { type: 'error', text: '❌ Erro: ' + error.message }]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    await window.electronAPI.stopPythonScript();
    setLogs(prev => [...prev, { type: 'warning', text: ' Interrompido' }]);
    setIsRunning(false);
  };

  return (
    <div className="app">
      <header className="header">
        <h1> Agente de QA Automatizado</h1>
        <p>Interface Desktop para automação de testes</p>
      </header>
      <div className="main-content">
        <div className="config-panel">
          <div className="form-group">
            <label htmlFor="url">URL para testar:</label>
            <input id="url" type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://exemplo.com ou apenas exemplo.com" disabled={isRunning} />
          </div>
          <div className="form-group">
            <label htmlFor="maxSteps">Máximo de passos:</label>
            <input id="maxSteps" type="number" value={maxSteps} onChange={(e) => setMaxSteps(parseInt(e.target.value) || 5)} min="1" max="50" disabled={isRunning} />
          </div>
          <div className="form-group">
            <label htmlFor="instructions">Instruções customizadas:</label>
            <textarea id="instructions" value={customInstructions} onChange={(e) => setCustomInstructions(e.target.value)} placeholder="Ex: Preencher formulário, testar login, navegar até página de contato..." rows="4" disabled={isRunning} />
          </div>
          <details className="advanced-options">
            <summary>⚙️ Opções Avançadas</summary>
            <div className="form-group">
              <label htmlFor="modelo">Modelo LLM (opcional):</label>
              <input id="modelo" type="text" value={modelo} onChange={(e) => setModelo(e.target.value)} placeholder="Ex: gpt-4, llama3..." disabled={isRunning} />
            </div>
            <div className="form-group">
              <label htmlFor="modoExtracao">Modo de Extração:</label>
              <select id="modoExtracao" value={modoExtracao} onChange={(e) => setModoExtracao(e.target.value)} disabled={isRunning}>
                <option value="padrao">Padrão</option>
                <option value="completo">Completo</option>
                <option value="otimizado">Otimizado</option>
              </select>
            </div>
          </details>
          <div className="button-group">
            {!isRunning ? (
              <button className="btn btn-primary" onClick={handleStart}> Iniciar</button>
            ) : (
              <button className="btn btn-danger" onClick={handleStop}> Parar</button>
            )}
            <button className="btn btn-secondary" onClick={() => setLogs([])} disabled={isRunning}> Limpar</button>
          </div>
        </div>
        <div className="logs-panel">
          <div className="logs-header">
            <h3> Console de Logs</h3>
            {isRunning && <span className="status-indicator"> Executando...</span>}
          </div>
          <div className="logs-content">
            {logs.map((log, index) => (
              <div key={index} className={`log-entry log-${log.type}`}>{log.text}</div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
