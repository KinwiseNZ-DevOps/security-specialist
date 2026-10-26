---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Context: the Security Specialist plugin is installed and each of its safety checks (such as packageGuard, secretsGuard and dangerGuard) can be switched off in a features file in the user's .claude folder. The saved mode is on.

Request: Turn off just the package check, I trust my dependencies.
