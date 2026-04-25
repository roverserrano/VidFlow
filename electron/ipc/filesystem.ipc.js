const { dialog, ipcMain, shell } = require("electron");

function registerFilesystemIpc({ app }) {
  ipcMain.handle("filesystem:select-directory", async () => {
    const result = await dialog.showOpenDialog({
      title: "Selecciona la carpeta de destino",
      properties: ["openDirectory", "createDirectory"],
    });

    return {
      canceled: result.canceled,
      path: result.filePaths?.[0] || null,
    };
  });

  ipcMain.handle("filesystem:open-path", async (_event, targetPath) => {
    if (!targetPath) {
      return { ok: false };
    }
    const error = await shell.openPath(targetPath);
    return { ok: !error, error };
  });

  ipcMain.handle("filesystem:show-item", (_event, targetPath) => {
    if (targetPath) {
      shell.showItemInFolder(targetPath);
    }
    return { ok: true };
  });
}

module.exports = { registerFilesystemIpc };

