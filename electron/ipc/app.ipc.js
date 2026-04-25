const { ipcMain, Notification } = require("electron");

function registerAppIpc({ app, backend }) {
  ipcMain.handle("app:get-info", () => ({
    name: "VidFlow",
    version: app.getVersion(),
    platform: process.platform,
  }));

  ipcMain.handle("backend:get-url", () => backend.url);

  ipcMain.handle("app:notify", (_event, payload) => {
    const title = payload?.title || "VidFlow";
    const body = payload?.body || "";
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
    }
    return { ok: true };
  });
}

module.exports = { registerAppIpc };

