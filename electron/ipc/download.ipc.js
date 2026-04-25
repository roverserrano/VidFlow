const { ipcMain } = require("electron");

async function backendJson(backend, path, options = {}) {
  const response = await fetch(`${backend.url}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || "Error en descarga");
  }
  return data;
}

function registerDownloadIpc({ backend }) {
  ipcMain.handle("downloads:analyze", (_event, payload) => backendJson(backend, "/metadata", {
    method: "POST",
    body: JSON.stringify(payload || {}),
  }));

  ipcMain.handle("downloads:start", (_event, payload) => backendJson(backend, "/downloads", {
    method: "POST",
    body: JSON.stringify(payload || {}),
  }));

  ipcMain.handle("downloads:cancel", (_event, jobId) => backendJson(backend, `/downloads/${jobId}/cancel`, {
    method: "POST",
  }));
}

module.exports = { registerDownloadIpc };

