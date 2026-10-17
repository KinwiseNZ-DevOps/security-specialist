// SessionStart hook: loads this plugin's always-on rules into the session.
// Settings live in always-on.config.json next to this file. The saved mode is
// one word (on, off or auto) in $CLAUDE_CONFIG_DIR/.<id>.mode (default ~/.claude).
// No file means the default mode (on). The user is told the state at the start
// of each session. Never blocks session start: any failure exits 0.
//
// Runs under Node so it works on macOS, Linux and Windows.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const MODES = ["on", "off", "auto"];

function readStdin(ms = 300) {
  if (process.stdin.isTTY) return Promise.resolve("");
  return new Promise((resolve) => {
    let data = "";
    const timer = setTimeout(() => resolve(data), ms);
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => {
      clearTimeout(timer);
      resolve(data);
    });
    process.stdin.on("error", () => resolve(data));
  });
}

function findMarker(dir, markers) {
  const roots = [dir];
  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory() && !entry.name.startsWith(".") && entry.name !== "node_modules") {
        roots.push(path.join(dir, entry.name));
      }
    }
  } catch {}
  for (const root of roots) {
    for (const marker of markers) {
      try {
        const file = path.join(root, marker.file);
        if (!fs.existsSync(file)) continue;
        if (marker.contains) {
          const text = fs.readFileSync(file, "utf8").toLowerCase();
          if (!text.includes(String(marker.contains).toLowerCase())) continue;
        }
        return path.relative(dir, file) || marker.file;
      } catch {}
    }
  }
  return null;
}

try {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const cfg = JSON.parse(fs.readFileSync(path.join(here, "always-on.config.json"), "utf8"));

  let source = "";
  try {
    source = JSON.parse(await readStdin()).source || "";
  } catch {}

  const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  const modePath = path.join(claudeDir, `.${cfg.id}.mode`);

  let mode = MODES.includes(cfg.defaultMode) ? cfg.defaultMode : "on";
  let saved = false;
  try {
    const raw = fs.readFileSync(modePath, "utf8").trim().toLowerCase();
    if (MODES.includes(raw)) {
      mode = raw;
      saved = true;
    }
  } catch {}
  if (!saved && cfg.legacyOffFile && fs.existsSync(path.join(claudeDir, cfg.legacyOffFile))) {
    mode = "off";
  }

  const project = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const ask = `ask me to set the saved mode to on, off or auto`;
  let active = false;
  let message = "";

  if (mode === "off") {
    message = `${cfg.name}: off. To turn it back on, ${ask}.`;
  } else if (mode === "auto" && cfg.autoDetect !== false) {
    const hit = findMarker(project, cfg.autoMarkers || []);
    if (hit) {
      active = true;
      message = `${cfg.name}: auto, active here (found ${hit}). Say "stop ${cfg.phrase} mode" to pause it, or ${ask}.`;
    } else {
      message = `${cfg.name}: auto, not active in this folder (no matching project files). To force it on, ${ask}.`;
    }
  } else {
    active = true;
    message = `${cfg.name}: ${mode === "auto" ? "auto, active" : "on"}. Say "stop ${cfg.phrase} mode" to pause it, or ${ask}.`;
  }

  const output = {};
  if (source !== "compact") output.systemMessage = message;

  if (active) {
    const rulesPath = path.join(here, "..", cfg.rules);
    if (fs.existsSync(rulesPath)) {
      const rules = fs.readFileSync(rulesPath, "utf8").replace(/(?:\r?\n)+$/, "");
      const controls =
        `\n\nMode controls (${cfg.name}, currently ${mode}): if the user says "stop ${cfg.phrase} mode", ` +
        `stop following the rules above until they say "start ${cfg.phrase} mode". If the user asks to change the saved mode, ` +
        `write exactly one word (on, off or auto) into ${modePath}, creating the file if needed, and confirm in one line. ` +
        `"auto" loads these rules only in projects that look relevant.`;
      output.hookSpecificOutput = {
        hookEventName: "SessionStart",
        additionalContext: `${rules}${controls}`,
      };
    }
  }

  if (output.systemMessage || output.hookSpecificOutput) {
    process.stdout.write(`${JSON.stringify(output)}\n`);
  }
} catch {
  process.exit(0);
}
