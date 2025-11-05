const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runPythonScript: (scriptPath, args) => ipcRenderer.invoke('run-python-script', scriptPath, args),
  stopPythonScript: () => ipcRenderer.invoke('stop-python-script'),
  fetchModels: (provider, llmUrl) => ipcRenderer.invoke('fetch-models', provider, llmUrl),
  onPythonOutput: (callback) => ipcRenderer.on('python-output', (event, data) => callback(data)),
  onPythonError: (callback) => ipcRenderer.on('python-error', (event, data) => callback(data)),
});
