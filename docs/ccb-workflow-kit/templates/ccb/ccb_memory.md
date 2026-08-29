# CCB Shared Project Memory — Team Workflow Contract

> Replace the placeholders below with project facts. Never put credentials, production addresses, customer data or private tokens here.

## Team roles

| Agent | Provider | Responsibility | Write permission |
| --- | --- | --- | --- |
| main | Codex | Owns workflow state, authorization checks and final claims | No code write by default |
| reviewer | Codex | Fresh, read-only review of exact-HEAD diff every round | Never |
| developer | Claude | The only implementation and repair writer | Its assigned worktree only |
| knowledge_keeper | Claude | Documents decisions after developer has stopped | Only after developer stops |
| task_scout | Claude | Read-only task and dependency reconnaissance | Never |
| explorer | Claude | Read-only code, contract and test mapping | Never |
| utility | Claude | Read-only deterministic commands and evidence | Never |

## Context discipline

- Clear the reviewer before every review round.
- Preserve developer context within one task, including review fixes.
- At the next task boundary, clear reused developer, knowledge_keeper, task_scout, explorer and utility agents.
- Never run developer and knowledge_keeper as concurrent writers in one worktree.

## Delegation contract

- Start every delegated message with `你是 <agent>（<role>）。`.
- Include: goal, scope/files, assumptions, expected output, verification, and whether writing is prohibited.
- Use ordinary `ask` when a result is needed; use `--chain` only for a true blocking dependency; use `--silence` only when no result is needed.
- Every result is concise: findings / changes / verification / blockers / risks.

## Project-specific rules — fill in before production use

- Base branch and branch naming: `<FILL_ME>`
- Required checks and test commands: `<FILL_ME>`
- Paths that must never be changed: `<FILL_ME>`
- Database migration and deployment gates: `<FILL_ME>`
- Commit, push, PR, release, external communication authorization: `<FILL_ME>`
