/**
 * SubTranslate — Electron Main Process
 * 
 * Launches the Python backend as a child process and serves the Vue.js frontend.
 */
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;

/**
 * Get the path to the backend executable.
 */
function getBackendPath() {
  const isDev = !app.isPackaged;

  if (isDev) {
    // In development, use the Python module directly
    return {
      cmd: 'python3',
      args: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
      cwd: path.join(__dirname, '..', 'backend'),
    };
  }

  // In production, use the bundled executable
  const platform = process.platform;
  const ext = platform === 'win32' ? '.exe' : '';
  const backendExe = path.join(
    process.resourcesPath,
    `backend${ext}`
  );

  return {
    cmd: backendExe,
    args: ['--host', '127.0.0.1', '--port', '8000'],
    cwd: process.resourcesPath,
  };
}

/**
 * Start the Python backend process.
 */
function startBackend() {
  const { cmd, args, cwd } = getBackendPath();

  console.log(`Starting backend: ${cmd} ${args.join(' ')} (cwd: ${cwd})`);

  // Build env with optional FFmpeg path for packaged mode
  const backendEnv = {
    ...process.env,
    PYTHONUNBUFFERED: '1',
    PYTHONIOENCODING: 'utf-8',
  };

  if (!app.isPackaged) {
    // Dev mode: FFmpeg is in project bin/
    const devFfmpeg = path.join(__dirname, '..', 'bin', 'ffmpeg');
    if (require('fs').existsSync(devFfmpeg)) {
      backendEnv.SUBTRANSLATE_FFMPEG_PATH = devFfmpeg;
    }
  } else {
    // Packaged mode: FFmpeg is in Resources/bin/
    const pkgFfmpeg = path.join(process.resourcesPath, 'bin', 'ffmpeg');
    if (require('fs').existsSync(pkgFfmpeg)) {
      backendEnv.SUBTRANSLATE_FFMPEG_PATH = pkgFfmpeg;
    }
  }

  backendProcess = spawn(cmd, args, {
    cwd,
    stdio: ['ignore', 'pipe', 'pipe'],
    env: backendEnv,
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    backendProcess = null;
  });
}

/**
 * Stop the Python backend process.
 */
function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend...');
    backendProcess.kill('SIGTERM');

    // Force kill after 5 seconds if it doesn't stop
    setTimeout(() => {
      if (backendProcess) {
        backendProcess.kill('SIGKILL');
        backendProcess = null;
      }
    }, 5000);
  }
}

/**
 * Create the main application window.
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 800,
    minWidth: 700,
    minHeight: 600,
    title: 'SubTranslate',
    backgroundColor: '#FFFFFF',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const isDev = !app.isPackaged;

  if (isDev) {
    // In development, load from Vite dev server
    mainWindow.loadURL('http://localhost:5173');
    // mainWindow.webContents.openDevTools();
  } else {
    // In production, load from built frontend files
    const frontendPath = path.join(__dirname, 'dist', 'index.html');
    mainWindow.loadFile(frontendPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  startBackend();

  // Wait a bit for the backend to start before opening the window
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
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('will-quit', () => {
  stopBackend();
});