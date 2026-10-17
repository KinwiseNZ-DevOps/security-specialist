// SessionStart hook: loads this plugin's always-on rules into the session.
// Settings live in always-on.config.json next to this file. The saved mode is
// one word (on, off or auto) in $CLAUDE_CONFIG_DIR/.<id>.mode (default ~/.claude).
// No file means the default mode (on). The user is told the state at the start
// of each session. Never blocks session start: any failure exits 0.
//
// Runs under Node so it works on macOS, Linux and Windows.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readStdinJson, resolveState, sweepOld } from "./common.mjs";

try {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const input = await readStdinJson();
  const state = resolveState(here, input.cwd);
  if (!state) process.exit(0);
  const { cfg, mode, hit, active, modePath, featuresPath } = state;

  sweepOld();

  const ask = "ask me to set the saved mode to on, off or auto";
  let message;
  if (mode === "off") {
    message = `${cfg.name}: off. To turn it back on, ${ask}.`;
  } else if (mode === "auto" && cfg.autoDetect !== false && !active) {
    message = `${cfg.name}: auto, not active in this folder (no matching project files). To force it on, ${ask}.`;
  } else if (mode === "auto" && cfg.autoDetect !== false) {
    message = `${cfg.name}: auto, active here (found ${hit}). Say "stop ${cfg.phrase} mode" to pause it, or ${ask}.`;
  } else {
    message = `${cfg.name}: ${mode === "auto" ? "auto, active" : "on"}. Say "stop ${cfg.phrase} mode" to pause it, or ${ask}.`;
  }

  const output = {};
  if (input.source !== "compact") output.systemMessage = message;

  if (active) {
    const rulesPath = path.join(here, "..", cfg.rules);
    if (fs.existsSync(rulesPath)) {
      const rules = fs.readFileSync(rulesPath, "utf8").replace(/(?:\r?\n)+$/, "");
      const controls =
        `\n\nMode controls (${cfg.name}, currently ${mode}): if the user says "stop ${cfg.phrase} mode", ` +
        `stop following the rules above until they say "start ${cfg.phrase} mode". If the user asks to change the saved mode, ` +
        `write exactly one word (on, off or auto) into ${modePath}, creating the file if needed, and confirm in one line. ` +
        `"auto" loads these rules only in projects that look relevant. ` +
        `Safety checks run as hooks and can be switched on or off one by one: if the user asks, write a JSON object such as ` +
        `{"dangerGuard": false} into ${featuresPath}. Feature names: dangerGuard, secretsGuard, packageGuard, licenseGuard, ` +
        `editSecurity, promptGuard, verifyReminder, linkGuard, sessionLog, autoCommit, styleGuard.`;
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
