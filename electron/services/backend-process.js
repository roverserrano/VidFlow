const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { spawn } = require("node:child_process");

const HOST = process.env.VIDFLOW_BACKEND_HOST || "127.0.0.1";
const PORT = Number(process.env.VIDFLOW_BACKEND_PORT || 8716);

function requestHealth(url) {
  return new Promise((resolve) => {
    const req = http.get(`${url}/health`, (res) => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.on("error", () => resolve(false));
    req.setTimeout(600, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function resolvePython(rootDir, isPackaged) {
  if (process.env.VIDFLOW_PYTHON) {
    return process.env.VIDFLOW_PYTHON;
  }

  if (isPackaged) {
    const bundled = process.platform === "win32"
      ? path.join(process.resourcesPath, "python", "python.exe")
      : path.join(process.resourcesPath, "python", "bin", "python3");
    if (fs.existsSync(bundled)) {
      return bundled;
    }
  }

  const venvPython = process.platform === "win32"
    ? path.join(rootDir, ".venv", "Scripts", "python.exe")
    : path.join(rootDir, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }

  return process.platform === "win32" ? "python" : "python3";
}

function resolveBundledBackend() {
  if (!process.resourcesPath) {
    return null;
  }

  const executable = process.platform === "win32" ? "vidflow-backend.exe" : "vidflow-backend";
  const candidate = path.join(process.resourcesPath, "python", process.platform, "vidflow-backend", executable);
  return fs.existsSync(candidate) ? candidate : null;
}

function createBackendProcess({ rootDir, isPackaged }) {
  let child = null;
  const url = `http://${HOST}:${PORT}`;

  return {
    url,

    async start() {
      if (await requestHealth(url)) {
        return;
      }

      const bundledBackend = isPackaged ? resolveBundledBackend() : null;
      const python = bundledBackend || resolvePython(rootDir, isPackaged);
      const args = bundledBackend ? [] : ["-m", "uvicorn", "backend.main:app", "--host", HOST, "--port", String(PORT)];
      const ffmpegName = process.platform === "win32" ? "ffmpeg.exe" : "ffmpeg";
      const bundledFfmpeg = process.resourcesPath
        ? path.join(process.resourcesPath, "bin", "ffmpeg", ffmpegName)
        : path.join(rootDir, "resources", "bin", "ffmpeg", ffmpegName);

      child = spawn(python, args, {
        cwd: isPackaged && process.resourcesPath ? process.resourcesPath : rootDir,
        env: {
          ...process.env,
          PYTHONPATH: rootDir,
          VIDFLOW_BACKEND_HOST: HOST,
          VIDFLOW_BACKEND_PORT: String(PORT),
          VIDFLOW_FFMPEG: fs.existsSync(bundledFfmpeg) ? bundledFfmpeg : (process.env.VIDFLOW_FFMPEG || ""),
        },
        stdio: "pipe",
        windowsHide: true,
      });

      child.stdout.on("data", (chunk) => console.log(`[backend] ${chunk}`.trim()));
      child.stderr.on("data", (chunk) => console.error(`[backend] ${chunk}`.trim()));

      for (let attempt = 0; attempt < 40; attempt += 1) {
        if (await requestHealth(url)) {
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 250));
      }

      throw new Error("No se pudo iniciar el backend local de VidFlow.");
    },

    stop() {
      if (child && !child.killed) {
        child.kill();
      }
      child = null;
    },
  };
}

module.exports = { createBackendProcess };
