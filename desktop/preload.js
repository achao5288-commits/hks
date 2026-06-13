/**
 * Preload script — exposes safe API bridge between Electron and renderer.
 * Uses contextBridge to isolate Node.js capabilities from the web content.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Get the backend server URL
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

  // Get app version
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // Platform info
  platform: process.platform,

  // File dialogs (safe, no direct filesystem access)
  showOpenDialog: (options) => ipcRenderer.invoke('dialog:open', options),
  showSaveDialog: (options) => ipcRenderer.invoke('dialog:save', options),

  // App events
  onMenuAction: (callback) => {
    ipcRenderer.on('menu-action', (event, action) => callback(action));
  },

  removeMenuActionListener: () => {
    ipcRenderer.removeAllListeners('menu-action');
  },

  // Drag & drop from OS (file paths dropped onto the window)
  onFileDrop: (callback) => {
    ipcRenderer.on('file-drop', (event, filePaths) => callback(filePaths));
  },
});
