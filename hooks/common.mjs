// Shared helpers for the always-on hook and the guard hook.
// Never throws to the caller for expected problems: hooks must fail open.

import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const MODES = ["on", "off", "auto"];

export const DEFAULT_FEATURES = {
  dangerGuard: true,
  secretsGuard: true,
  packageGuard: true,
  licenseGuard: true,
  editSecurity: true,
  promptGuard: true,
  verifyReminder: true,
  linkGuard: false,
  sessionLog: false,
  autoCommit: false,
  styleGuard: false,
};

export function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return null;
  }
}

export function claudeDir() {
  return process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
}

export async function readStdin(ms = 300) {
  if (process.stdin.isTTY) return "";
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

export async function readStdinJson() {
  try {
    return JSON.parse(await readStdin()) || {};
  } catch {
    return {};
  }
}

export function findMarker(dir, markers) {
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

// Works out the saved mode, whether the plugin is active in this project, and
// which guard features are switched on.
export function resolveState(here, projectDir) {
  const cfg = readJson(path.join(here, "always-on.config.json"));
  if (!cfg) return null;
  const dir = claudeDir();
  const modePath = path.join(dir, `.${cfg.id}.mode`);
  const featuresPath = path.join(dir, `.${cfg.id}.features.json`);

  let mode = MODES.includes(cfg.defaultMode) ? cfg.defaultMode : "on";
  let saved = false;
  try {
    const raw = fs.readFileSync(modePath, "utf8").trim().toLowerCase();
    if (MODES.includes(raw)) {
      mode = raw;
      saved = true;
    }
  } catch {}
  if (!saved && cfg.legacyOffFile && fs.existsSync(path.join(dir, cfg.legacyOffFile))) mode = "off";

  const project = projectDir || process.env.CLAUDE_PROJECT_DIR || process.cwd();
  let active = false;
  let hit = null;
  if (mode === "on") active = true;
  else if (mode === "auto") {
    if (cfg.autoDetect === false) active = true;
    else {
      hit = findMarker(project, cfg.autoMarkers || []);
      active = Boolean(hit);
    }
  }

  const features = { ...DEFAULT_FEATURES, ...(cfg.features || {}) };
  const overrides = readJson(featuresPath);
  if (overrides && typeof overrides === "object") {
    for (const [key, value] of Object.entries(overrides)) {
      if (key in features && typeof value === "boolean") features[key] = value;
    }
  }

  return { cfg, mode, saved, active, hit, project, modePath, featuresPath, features };
}

function claimDir() {
  return path.join(os.tmpdir(), "claude-plugin-guards");
}

// Several plugins carry the same guards. The first one to claim a key does the
// work, so the user sees one prompt and one message and not one per plugin.
export function claim(key) {
  try {
    const dir = claimDir();
    fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, crypto.createHash("sha1").update(key).digest("hex"));
    fs.writeFileSync(file, "1", { flag: "wx" });
    return true;
  } catch (error) {
    return error && error.code !== "EEXIST";
  }
}

export function sweepOld(maxAgeMs = 24 * 60 * 60 * 1000) {
  try {
    const dir = claimDir();
    const now = Date.now();
    for (const name of fs.readdirSync(dir)) {
      const file = path.join(dir, name);
      try {
        if (now - fs.statSync(file).mtimeMs > maxAgeMs) fs.unlinkSync(file);
      } catch {}
    }
  } catch {}
}

function statePath(sessionId) {
  const id = crypto.createHash("sha1").update(String(sessionId || "none")).digest("hex").slice(0, 16);
  return path.join(claimDir(), `state-${id}.json`);
}

export function readState(sessionId) {
  return readJson(statePath(sessionId)) || {};
}

export function writeState(sessionId, state) {
  try {
    fs.mkdirSync(claimDir(), { recursive: true });
    fs.writeFileSync(statePath(sessionId), JSON.stringify(state));
  } catch {}
}
