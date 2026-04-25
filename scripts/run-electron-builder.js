const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const builder = process.platform === "win32"
  ? path.join(root, "node_modules", ".bin", "electron-builder.cmd")
  : path.join(root, "node_modules", ".bin", "electron-builder");

const result = spawnSync(builder, process.argv.slice(2), {
  cwd: root,
  stdio: "inherit",
  env: {
    ...process.env,
    ELECTRON_BUILDER_CACHE: path.join(root, ".cache", "electron-builder")
  }
});

process.exit(result.status ?? 1);

