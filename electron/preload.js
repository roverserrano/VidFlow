const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("vidflow", {
  appInfo: () => ipcRenderer.invoke("app:get-info"),
  backendUrl: () => ipcRenderer.invoke("backend:get-url"),
  notify: (payload) => ipcRenderer.invoke("app:notify", payload),

  config: {
    get: () => ipcRenderer.invoke("config:get"),
    patch: (payload) => ipcRenderer.invoke("config:patch", payload),
  },

  downloads: {
    analyze: (url) => ipcRenderer.invoke("downloads:analyze", { url }),
    start: (payload) => ipcRenderer.invoke("downloads:start", payload),
    cancel: (jobId) => ipcRenderer.invoke("downloads:cancel", jobId),
  },

  filesystem: {
    selectDirectory: () => ipcRenderer.invoke("filesystem:select-directory"),
    openPath: (targetPath) => ipcRenderer.invoke("filesystem:open-path", targetPath),
    showItem: (targetPath) => ipcRenderer.invoke("filesystem:show-item", targetPath),
  },
});

