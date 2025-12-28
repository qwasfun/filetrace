const { contextBridge, ipcRenderer } = require('electron')

console.log('Preload script loaded')

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: () => ipcRenderer.invoke('select-file'),
  selectFiles: () => ipcRenderer.invoke('select-files'),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  getFolderFiles: (folderPath) => ipcRenderer.invoke('get-folder-files', folderPath),
  getFileInfo: (filePath) => ipcRenderer.invoke('get-file-info', filePath),
  getFilesInfo: (filePaths) => ipcRenderer.invoke('get-files-info', filePaths),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
})

console.log('electronAPI exposed to window')
