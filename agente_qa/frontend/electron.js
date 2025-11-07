const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let pythonProcess = null;
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 600,  // Permite redimensionar para telas menores
    minHeight: 500, // Permite redimensionar para telas menores
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Em desenvolvimento, carrega do Vite dev server
  // Em produção, carrega do dist (após npm run build)
  const isDev = !app.isPackaged && process.env.NODE_ENV !== 'production';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173').catch((err) => {
      console.error('Error loading dev server:', err);
      console.log('Make sure Vite dev server is running on port 5173 (npm run dev)');
    });
  } else {
    const htmlPath = path.join(__dirname, 'dist', 'index.html');
    mainWindow.loadFile(htmlPath).catch((err) => {
      console.error('Error loading file:', err);
    });
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Iniciar watcher de arquivos de logs (monitora novos passos/respostas)
  try {
    // electron.js está em agente_qa/frontend, então precisamos voltar 2 níveis para AgenteIA
    const projectRoot = path.join(__dirname, '..', '..');
    const logsDir = path.join(projectRoot, 'llm_agent_test', 'logs', 'model_responses');
    
    console.log('[Watcher] Monitorando diretório:', logsDir);
    
    if (fs.existsSync(logsDir)) {
      // Usamos fs.watch para notificar renderer sobre novos arquivos
      fs.watch(logsDir, { persistent: true }, (eventType, filename) => {
        if (!filename) return;
        const f = filename.toString();
        if (!f.toLowerCase().endsWith('.json')) return;
        
        console.log(`[Watcher] Evento detectado: ${eventType} - ${f}`);
        
        try {
          const full = path.join(logsDir, f);
          const stats = fs.existsSync(full) ? fs.statSync(full) : null;
          const payload = { name: f, path: full, mtime: stats ? stats.mtimeMs : Date.now(), eventType };
          if (mainWindow && mainWindow.webContents) {
            console.log(`[Watcher] Enviando evento 'step-log-changed' para renderer`);
            mainWindow.webContents.send('step-log-changed', payload);
          }
        } catch (e) {
          console.error('[Watcher] erro ao processar evento:', e);
        }
      });
      console.log('[Watcher] ✓ Watcher iniciado com sucesso');
    } else {
      console.error('[Watcher] ⚠️ Diretório não existe:', logsDir);
    }
  } catch (e) {
    console.error('[Watcher] falha ao iniciar watcher de logs:', e);
  }
}

ipcMain.handle('run-python-script', async (event, scriptPath, args = []) => {
  return new Promise((resolve) => {
    const pythonPath = path.join(__dirname, '..', '..', '.venv', 'Scripts', 'python.exe');
    const projectRoot = path.join(__dirname, '..', '..');
    
    const scriptCandidates = [
      path.join(projectRoot, 'llm_agent_test', 'main.py'),
      path.join(projectRoot, 'agente_qa', 'main.py'),
      path.join(projectRoot, 'main.py')
    ];
    
    let scriptFullPath = null;
    for (const candidate of scriptCandidates) {
      if (fs.existsSync(candidate)) {
        scriptFullPath = candidate;
        break;
      }
    }
    
    if (!scriptFullPath) {
      const error = `Script not found. Tried: ${scriptCandidates.join(', ')}`;
      event.sender.send('python-error', error);
      resolve({ success: false, error });
      return;
    }
    
    // Configurar ambiente para UTF-8
    const pythonEnv = {
      ...process.env,
      PYTHONIOENCODING: 'utf-8',
      PYTHONUTF8: '1'
    };
    
    pythonProcess = spawn(pythonPath, [scriptFullPath, ...args], {
      env: pythonEnv,
      encoding: 'utf-8'
    });
    
    pythonProcess.stdout.setEncoding('utf8');
    pythonProcess.stderr.setEncoding('utf8');
    
    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('[Python stdout]:', output);
      event.sender.send('python-output', output);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.log('[Python stderr]:', error);
      event.sender.send('python-error', error);
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`[Python] Process exited with code ${code}`);
      event.sender.send('python-output', `\n[Processo finalizado com código ${code}]\n`);
      pythonProcess = null;
    });
    
    resolve({ success: true });
  });
});

ipcMain.handle('stop-python-script', async () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    return { success: true };
  }
  return { success: false, error: 'No process running' };
});

ipcMain.handle('fetch-models', async (event, provider, llmUrl) => {
  try {
    let url;
    
    // Determinar endpoint baseado no provider
    if (provider === 'lmstudio_local') {
      url = `${llmUrl}/v1/models`;
    } else if (provider === 'ollama_local') {
      url = `${llmUrl}/api/tags`;
    } else if (provider === 'api_externa') {
      url = `${llmUrl}/models`;
    } else {
      return { success: false, error: 'Provider desconhecido' };
    }
    
    console.log(`[Fetch Models] Buscando modelos de: ${url}`);
    
    const https = require('https');
    const http = require('http');
    const urlModule = require('url');
    const parsedUrl = urlModule.parse(url);
    const protocol = parsedUrl.protocol === 'https:' ? https : http;
    
    return new Promise((resolve) => {
      const req = protocol.get(url, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const jsonData = JSON.parse(data);
            let models = [];
            
            // Parsear resposta baseado no provider
            if (provider === 'lmstudio_local' || provider === 'api_externa') {
              // Formato OpenAI: { data: [{ id: "model-name" }] }
              models = jsonData.data ? jsonData.data.map(m => m.id) : [];
            } else if (provider === 'ollama_local') {
              // Formato Ollama: { models: [{ name: "model-name" }] }
              models = jsonData.models ? jsonData.models.map(m => m.name) : [];
            }
            
            console.log(`[Fetch Models] Modelos encontrados: ${models.length}`);
            resolve({ success: true, models });
          } catch (parseError) {
            console.error('[Fetch Models] Erro ao parsear JSON:', parseError);
            resolve({ success: false, error: 'Erro ao parsear resposta', details: parseError.message });
          }
        });
      });
      
      req.on('error', (error) => {
        console.error('[Fetch Models] Erro na requisição:', error);
        resolve({ success: false, error: 'Erro ao conectar com servidor', details: error.message });
      });
      
      req.setTimeout(5000, () => {
        req.destroy();
        resolve({ success: false, error: 'Timeout ao buscar modelos' });
      });
    });
  } catch (error) {
    console.error('[Fetch Models] Erro geral:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('fetch-step-logs', async (event, stepFiles) => {
  const projectRoot = path.join(__dirname, '..', '..');
  const payloadsDir = path.join(projectRoot, 'llm_agent_test', 'logs', 'payloads');
  
  const results = [];
  for (const file of stepFiles) {
    try {
      // Ler resposta do modelo (SAÍDA)
      const responseData = fs.readFileSync(file, 'utf-8');
      const response = JSON.parse(responseData);
      
      // Extrair informações do nome do arquivo de resposta
      // Formato: passo9_qwen3-vl-4b-instruct_20251107_081233.json
      const fileName = path.basename(file);
      const match = fileName.match(/^passo(\d+)_(.+?)_(\d{8}_\d{6})\.json$/);
      
      let payload = null;
      
      if (match) {
        const stepNum = match[1];
        const modelName = match[2];
        const responseTimestamp = match[3];
        
        console.log(`[fetch-step-logs] Buscando payload para passo ${stepNum}, modelo ${modelName}, timestamp ~${responseTimestamp}`);
        
        // Estratégia 1: Tentar timestamp exato
        const exactPayloadName = `${modelName}_${responseTimestamp}.json`;
        const exactPayloadPath = path.join(payloadsDir, exactPayloadName);
        
        if (fs.existsSync(exactPayloadPath)) {
          try {
            const payloadData = fs.readFileSync(exactPayloadPath, 'utf-8');
            payload = JSON.parse(payloadData);
            console.log(`[fetch-step-logs] ✓ Payload encontrado (timestamp exato): ${exactPayloadName}`);
          } catch (e) {
            console.error(`[fetch-step-logs] Erro ao ler payload exato:`, e);
          }
        } else {
          // Estratégia 2: Buscar payload com mesmo modelo e timestamp próximo
          try {
            const allPayloads = fs.readdirSync(payloadsDir)
              .filter(f => f.startsWith(modelName) && f.endsWith('.json'))
              .map(f => {
                const payloadMatch = f.match(/^.+_(\d{8}_\d{6})\.json$/);
                if (payloadMatch) {
                  const payloadTimestamp = payloadMatch[1];
                  const payloadPath = path.join(payloadsDir, f);
                  const stats = fs.statSync(payloadPath);
                  return {
                    name: f,
                    path: payloadPath,
                    timestamp: payloadTimestamp,
                    mtime: stats.mtimeMs
                  };
                }
                return null;
              })
              .filter(p => p !== null);
            
            // Ordenar por timestamp (mais próximo do responseTimestamp)
            allPayloads.sort((a, b) => {
              const diffA = Math.abs(parseInt(a.timestamp.replace(/[_]/g, '')) - parseInt(responseTimestamp.replace(/[_]/g, '')));
              const diffB = Math.abs(parseInt(b.timestamp.replace(/[_]/g, '')) - parseInt(responseTimestamp.replace(/[_]/g, '')));
              return diffA - diffB;
            });
            
            if (allPayloads.length > 0) {
              const closestPayload = allPayloads[0];
              const payloadData = fs.readFileSync(closestPayload.path, 'utf-8');
              payload = JSON.parse(payloadData);
              console.log(`[fetch-step-logs] ✓ Payload encontrado (timestamp próximo): ${closestPayload.name}`);
            } else {
              console.log(`[fetch-step-logs] ✗ Nenhum payload encontrado para modelo ${modelName}`);
            }
          } catch (e) {
            console.error(`[fetch-step-logs] Erro ao buscar payload próximo:`, e);
          }
        }
      }
      
      // Retorna objeto combinado
      results.push({
        response: response,     // Dados de SAÍDA (model_responses)
        payload: payload,       // Dados de ENTRADA (payloads)
        responsePath: file,
        payloadPath: payload ? 'encontrado' : 'não encontrado'
      });
    } catch (e) {
      results.push({ erro: `Falha ao ler ${file}: ${e.message}` });
    }
  }
  return results;
});

// Lista os arquivos de passos em logs/model_responses e retorna metadados
ipcMain.handle('list-step-logs', async () => {
  try {
    // electron.js está em agente_qa/frontend
    // Caminho correto: llm_agent_test/logs/model_responses
    const projectRoot = path.join(__dirname, '..', '..');
    const logsDir = path.join(projectRoot, 'llm_agent_test', 'logs', 'model_responses');
    
    console.log('[list-step-logs] Buscando logs em:', logsDir);
    console.log('[list-step-logs] Diretório existe?', fs.existsSync(logsDir));
    
    if (!fs.existsSync(logsDir)) return { success: true, files: [] };

    const files = fs.readdirSync(logsDir)
      .filter(f => f.toLowerCase().endsWith('.json'))
      .map(f => {
        const full = path.join(logsDir, f);
        const stats = fs.statSync(full);
        return { name: f, path: full, mtime: stats.mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime); // MAIS RECENTES PRIMEIRO (ordem DECRESCENTE)

    console.log(`[list-step-logs] Encontrados ${files.length} arquivos`);
    if (files.length > 0) {
      console.log('[list-step-logs] Arquivo mais recente:', files[0].name);
    }
    return { success: true, files };
  } catch (e) {
    console.error('[list-step-logs] Erro ao listar arquivos:', e);
    return { success: false, error: e.message };
  }
});

// Handler para selecionar pasta de logs via diálogo
ipcMain.handle('select-logs-folder', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
      title: 'Selecione a pasta raiz dos logs',
      buttonLabel: 'Selecionar Pasta'
    });
    
    if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
      return { success: false, canceled: true };
    }
    
    const selectedPath = result.filePaths[0];
    console.log('[select-logs-folder] Pasta selecionada:', selectedPath);
    return { success: true, path: selectedPath };
  } catch (e) {
    console.error('[select-logs-folder] Erro ao abrir diálogo:', e);
    return { success: false, error: e.message };
  }
});

// Handler para varrer subpastas dentro da pasta selecionada
ipcMain.handle('scan-logs-folder', async (event, rootPath) => {
  try {
    console.log('[scan-logs-folder] Varrendo pasta:', rootPath);
    
    if (!fs.existsSync(rootPath)) {
      return { success: false, error: 'Pasta não existe' };
    }
    
    const folders = [];
    const items = fs.readdirSync(rootPath, { withFileTypes: true });
    
    for (const item of items) {
      if (item.isDirectory()) {
        const folderPath = path.join(rootPath, item.name);
        
        // Conta quantos arquivos JSON tem nesta subpasta
        let jsonCount = 0;
        try {
          const files = fs.readdirSync(folderPath);
          jsonCount = files.filter(f => f.toLowerCase().endsWith('.json')).length;
        } catch (e) {
          console.error(`[scan-logs-folder] Erro ao ler ${folderPath}:`, e);
        }
        
        folders.push({
          name: item.name,
          path: folderPath,
          fileCount: jsonCount
        });
      }
    }
    
    // Ordena por nome
    folders.sort((a, b) => a.name.localeCompare(b.name));
    
    console.log(`[scan-logs-folder] Encontradas ${folders.length} subpastas`);
    return { success: true, folders };
  } catch (e) {
    console.error('[scan-logs-folder] Erro ao varrer pasta:', e);
    return { success: false, error: e.message };
  }
});

// Handler modificado para listar logs de uma pasta customizada
ipcMain.handle('list-step-logs-from-folder', async (event, folderPath) => {
  try {
    console.log('[list-step-logs-from-folder] Buscando logs em:', folderPath);
    
    if (!fs.existsSync(folderPath)) {
      return { success: false, error: 'Pasta não existe' };
    }

    const files = fs.readdirSync(folderPath)
      .filter(f => f.toLowerCase().endsWith('.json'))
      .map(f => {
        const full = path.join(folderPath, f);
        const stats = fs.statSync(full);
        return { name: f, path: full, mtime: stats.mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime); // MAIS RECENTES PRIMEIRO

    console.log(`[list-step-logs-from-folder] Encontrados ${files.length} arquivos`);
    return { success: true, files };
  } catch (e) {
    console.error('[list-step-logs-from-folder] Erro ao listar arquivos:', e);
    return { success: false, error: e.message };
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});