const { app, BrowserWindow } = require('electron');
const path = require('path');

console.log('===== ELECTRON INICIANDO =====');
console.log('Diretório:', __dirname);
console.log('Versão Electron:', process.versions.electron);

let mainWindow = null;

function createWindow() {
  console.log('Criando janela...');
  
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: '#1e1e1e',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const htmlPath = path.join(__dirname, 'dist', 'index.html');
  console.log('Carregando HTML de:', htmlPath);
  
  mainWindow.loadFile(htmlPath)
    .then(() => console.log('HTML carregado com sucesso!'))
    .catch((err) => console.error('ERRO ao carregar HTML:', err));
  
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Página carregou!');
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('ERRO no carregamento:', errorCode, errorDescription);
  });
  
  mainWindow.on('closed', () => {
    console.log('Janela fechada');
    mainWindow = null;
  });
  
  console.log('Janela criada!');
}

app.whenReady().then(() => {
  console.log('App pronto!');
  createWindow();
});

app.on('window-all-closed', () => {
  console.log('Todas janelas fechadas');
  app.quit();
});

app.on('will-quit', () => {
  console.log('App vai fechar');
});

console.log('===== SCRIPT CARREGADO =====');
