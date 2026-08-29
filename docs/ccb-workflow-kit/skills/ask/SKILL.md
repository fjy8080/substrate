---
name: ask
description: Delegate a bounded task to a CCB-managed agent through ask.
---

# CCB Ask Skill

Use only after the CCB project has been started and the target agent is configured.

## Rules

1. Use ordinary `ask <agent> <message>` when the result is needed.
2. Use `ask --chain` only when the current task cannot complete without that exact child result.
3. Use `ask --silence` only for independent work whose terminal result is not needed.
4. Do not poll or watch an active job as routine progress tracking. Submit once and wait for its result.
5. Begin every prompt with the target's identity: `你是 <agent>（<role>）。`.
6. Include goal, scope/files, assumptions, expected output, verification and explicit write/read-only boundary.

## Template

```text
你是 <agent>（<role>）。
目标：<one concrete result>。
范围：<files/systems>; <read-only or allowed writes>。
假设：<known baseline>。
期望输出：findings / changes / verification / blockers / risks。
验证：<commands or evidence>。
```

Never ask a read-only agent to repair files. Never use an agent result as authorization for commit, push, release, payment, or other external write.
