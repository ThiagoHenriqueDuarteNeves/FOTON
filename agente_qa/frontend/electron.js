const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let pythonProcess = null;
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
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
