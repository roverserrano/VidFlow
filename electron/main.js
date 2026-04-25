const path = require("node:path");
const { app, BrowserWindow, nativeTheme } = require("electron");

const { createBackendProcess } = require("./services/backend-process");
const { registerAppIpc } = require("./ipc/app.ipc");
const { registerConfigIpc } = require("./ipc/config.ipc");
const { registerDownloadIpc } = require("./ipc/download.ipc");
const { registerFilesystemIpc } = require("./ipc/filesystem.ipc");

const isDev = !app.isPackaged;
const backend = createBackendProcess({
  rootDir: path.resolve(__dirname, ".."),
  isPackaged: app.isPackaged,
});

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 900,
    minHeight: 600,
    title: "VidFlow",
    backgroundColor: nativeTheme.shouldUseDarkColors ? "#101319" : "#f4f1ea",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());

  if (isDev) {
    mainWindow.loadURL(process.env.VIDFLOW_RENDERER_URL || "http://localhost:5173");
    mainWindow.webContents.openDevTools({ mode: "detach" });
  } else {
    mainWindow.loadFile(path.join(__dirname, "..", "renderer", "dist", "index.html"));
  }
}

app.whenReady().then(async () => {
  registerAppIpc({ app, backend });
  registerConfigIpc({ backend });
  registerDownloadIpc({ backend });
  registerFilesystemIpc({ app });

  await backend.start();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  backend.stop();
});

