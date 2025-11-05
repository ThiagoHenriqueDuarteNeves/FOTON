const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let pythonProcess = null;
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const htmlPath = path.join(__dirname, 'dist', 'index.html');
  
  mainWindow.loadFile(htmlPath).catch((err) => {
    console.error('Error loading file:', err);
  });
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
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
