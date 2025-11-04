const { app, BrowserWindow } = require('electron');
const path = require('path');

console.log('=== ELECTRON TEST STARTING ===');
console.log('Process ID:', process.pid);
console.log('Electron version:', process.versions.electron);

let win = null;

function createWindow() {
  console.log('Creating window...');
  
  win = new BrowserWindow({
    width: 800,
    height: 600,
    backgroundColor: '#2e2c29',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  console.log('Window created, loading HTML...');
  
  win.loadURL('data:text/html,<html><body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-family: Arial; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;"><h1>🎉 Electron está funcionando!</h1></body></html>');
  
  win.webContents.on('did-finish-load', () => {
    console.log('Page loaded successfully!');
  });

  win.on('closed', () => {
    console.log('Window closed');
    win = null;
  });
  
  console.log('Window setup complete');
}

app.whenReady().then(() => {
  console.log('App is ready');
  createWindow();
});

app.on('window-all-closed', () => {
  console.log('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  console.log('App activated');
  if (win === null) {
    createWindow();
  }
});

console.log('=== ELECTRON TEST SCRIPT LOADED ===');
