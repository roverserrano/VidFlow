const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const candidates = process.platform === "win32"
  ? [
      path.join(root, ".venv", "Scripts", "python.exe"),
      "python",
      "py"
    ]
  : [
      path.join(root, ".venv", "bin", "python"),
      "python3",
      "python"
    ];

const python = candidates.find((candidate) => candidate.includes(path.sep) ? fs.existsSync(candidate) : true);
const result = spawnSync(python, process.argv.slice(2), {
  cwd: root,
  stdio: "inherit",
  env: process.env
});

process.exit(result.status ?? 1);

