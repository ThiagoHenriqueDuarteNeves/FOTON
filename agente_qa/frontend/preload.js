const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runPythonScript: (scriptPath, args) => ipcRenderer.invoke('run-python-script', scriptPath, args),
  stopPythonScript: () => ipcRenderer.invoke('stop-python-script'),
  fetchModels: (provider, llmUrl) => ipcRenderer.invoke('fetch-models', provider, llmUrl),
  onPythonOutput: (callback) => ipcRenderer.on('python-output', (event, data) => callback(data)),
  onPythonError: (callback) => ipcRenderer.on('python-error', (event, data) => callback(data)),
  fetchStepLogs: (stepFiles) => ipcRenderer.invoke('fetch-step-logs', stepFiles),
  listStepLogs: () => ipcRenderer.invoke('list-step-logs'),
  onStepLogChanged: (callback) => ipcRenderer.on('step-log-changed', (event, data) => callback(data)),
  // Novos métodos para seleção de pasta de logs
  selectLogsFolder: () => ipcRenderer.invoke('select-logs-folder'),
  scanLogsFolder: (rootPath) => ipcRenderer.invoke('scan-logs-folder', rootPath),
  listStepLogsFromFolder: (folderPath) => ipcRenderer.invoke('list-step-logs-from-folder', folderPath)
});
