---
name: ccb-diagnose
description: Perform bounded, read-only diagnosis of a CCB agent or provider startup issue.
---

# CCB Diagnosis

Use only when an agent is stuck, disconnected, crashes on startup, or reports provider errors.

## Safe sequence

1. Confirm the current project directory and that no important task is active.
2. Run `ccb doctor`.
3. Run `ccb ping <agent>` only as a diagnosis.
4. Independently run the relevant provider CLI (`codex`, `claude`, or `opencode`) to determine whether the fault is CCB, PATH, login, model access, or provider client.
5. Report concise evidence and the smallest safe recovery action.

## Recovery boundaries

- `ccb restart <agent>` only for an idle configured agent.
- Use `ccb kill` only after confirming the directory is the intended project.
- Do not copy session/auth/provider-state files between machines.
- Do not expose tokens, cookies, `.env`, database files or raw provider logs in a report.
