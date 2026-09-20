---
name: ccb-clear
description: Reset CCB-managed provider context at a genuine task or review boundary.
---

# CCB Context Reset

`ccb clear <agent>` sends a provider-native reset to the selected managed agent. It does not delete project files or runtime state.

## When to use

- Before every reviewer round: `ccb clear reviewer`.
- After one task is actually complete and before reusing developer, knowledge_keeper, task_scout, explorer or utility on a new task.

## When not to use

- Between implementation and review-fix turns of one task; preserve developer context.
- While an agent has an active job.
- To solve an authentication, crash or configuration problem; use diagnostics first.

After clearing a reviewer, submit a complete new review request containing the exact commit/diff scope.
