/**
 * Electron main process.
 * Creates the application window and manages the Python backend subprocess.
 */
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;

const BACKEND_PORT = 8000;
const FRONTEND_URL = 'http://localhost:5173';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    title: 'Workflow Automation - 拖拽式工作流自动化',
    icon: path.join(__dirname, '..', 'frontend', 'public', 'favicon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
    backgroundColor: '#111118',
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Load frontend dev server
  mainWindow.loadURL(FRONTEND_URL);

  // Open DevTools in dev mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const backendDir = path.join(__dirname, '..', 'backend');

  backendProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
    cwd: backendDir,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error('[Backend] Failed to start:', err.message);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    backendProcess = null;
  });

  console.log(`[Backend] Starting on port ${BACKEND_PORT}...`);
}

function stopBackend() {
  if (backendProcess) {
    console.log('[Backend] Sending SIGTERM...');
    if (process.platform === 'win32') {
      backendProcess.kill();
    } else {
      backendProcess.kill('SIGTERM');
    }

    // Force kill after 5 seconds
    const forceKillTimeout = setTimeout(() => {
      if (backendProcess) {
        console.log('[Backend] Force killing...');
        backendProcess.kill('SIGKILL');
      }
    }, 5000);

    backendProcess.on('close', () => {
      clearTimeout(forceKillTimeout);
    });
  }
}

// ---- IPC Handlers ----

ipcMain.handle('get-backend-url', () => {
  return `http://localhost:${BACKEND_PORT}`;
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// ---- App Lifecycle ----

app.whenReady().then(() => {
  startBackend();

  // Give backend a moment to start, then create window
  setTimeout(() => {
    createWindow();
  }, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('quit', () => {
  stopBackend();
});
