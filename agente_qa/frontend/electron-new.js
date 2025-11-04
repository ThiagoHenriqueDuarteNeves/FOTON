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
    
    pythonProcess = spawn(pythonPath, [scriptFullPath, ...args]);
    
    pythonProcess.stdout.on('data', (data) => {
      event.sender.send('python-output', data.toString());
    });
    
    pythonProcess.stderr.on('data', (data) => {
      event.sender.send('python-error', data.toString());
    });
    
    pythonProcess.on('close', (code) => {
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
