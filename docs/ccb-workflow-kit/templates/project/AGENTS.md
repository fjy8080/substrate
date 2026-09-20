# AGENTS.md — Project-wide Agent Rules

> Replace every `<FILL_ME>` before use. This file is intentionally generic and contains no project facts or credentials.

## Mandatory workflow

- Read this file and the project build/test documentation before acting.
- Start every new task from the current integration baseline in a dedicated feature branch/worktree.
- `developer` is the only code writer in CCB. All other listed research/review roles are read-only.
- Never edit `.env` or secrets. Never hand-edit database schema; use the project's migration process.
- Commit, push, PR creation/merge, release, deployment and external writes need explicit authorization.

## Project commands

- Setup: `<FILL_ME>`
- Build: `<FILL_ME>`
- Unit test: `<FILL_ME>`
- Integration test: `<FILL_ME>`
- Lint/typecheck: `<FILL_ME>`

## Architecture and contract boundaries

- Stable public API/CLI contract: `<FILL_ME>`
- Database migration policy: `<FILL_ME>`
- Deployment/production gate: `<FILL_ME>`
- Documentation authority: `<FILL_ME>`

## CCB collaboration

- Every reviewer round starts after `ccb clear reviewer`.
- Same task: keep developer context through implementation and review repair.
- New task: clear reused agents only after previous task has truly completed.
- Do not concurrently run developer and knowledge_keeper as writers in one worktree.
