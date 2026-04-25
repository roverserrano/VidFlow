const { ipcMain } = require("electron");

async function backendJson(backend, path, options = {}) {
  const response = await fetch(`${backend.url}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message || "Error de configuracion");
  }
  return data;
}

function registerConfigIpc({ backend }) {
  ipcMain.handle("config:get", () => backendJson(backend, "/settings"));
  ipcMain.handle("config:patch", (_event, payload) => backendJson(backend, "/settings", {
    method: "PATCH",
    body: JSON.stringify(payload || {}),
  }));
}

module.exports = { registerConfigIpc };

