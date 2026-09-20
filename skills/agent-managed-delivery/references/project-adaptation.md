# Project adaptation

Inspect each repository before initializing the workflow. Do not assume branch names, remotes, CI names, package managers, PR templates, memory paths, or approval rules.
Do not assume PR body metadata is static: inspect PR templates, workflow triggers, validation scripts,
and live PR bodies for base/commit/file/HEAD fields that must change after every push.

Resolve in this order:

1. System/developer instructions and repository `AGENTS.md` files.
2. Current code, authoritative documents, real configuration, and live external state.
3. Explicit user authorization for the current batch.
4. Local memory and historical records.

For task scope, interpret repository sources with an additional ownership rule:

1. The WBS independent output, acceptance criteria, and test requirement define **what this task owns**.
2. Authoritative contracts and architecture define **how that owned output must behave**.
3. Adjacent predecessor, successor, and parallel WBS rows define explicit exclusions and dependency assumptions.
4. A broad authoritative-input citation never authorizes implementing every capability in that document.

Record this interpretation through `scope-record`. If the sources cannot be reconciled without changing WBS ownership, enter `SCOPE_BLOCKED` and request the user's decision; do not invent a project-specific redesign.

Map repository-specific rules into the closest public state without inventing new states. Examples:

- contract-before-code rules belong inside `EXPLORING` before `DEVELOPING`;
- a project task-report checkpoint belongs inside `DOCUMENTING` before `PR_CREATING`;
- release/security sign-off remains separate from a task PR merge unless explicitly delegated by the governing rule.

Always report an adapted gate, its source, and whether it changes an authorization threshold. If a project rule conflicts with delegated autonomy, the project rule wins until the user or authorized project owner explicitly changes it.

Repository-specific path conventions belong in `allowed_paths`. A new HEAD touching an unapproved path cannot pass `scope-check`; update the scope only after explicit user approval, including in delegated mode.

Store workflow state in the repository's private Git common directory through `workflowctl.py`. This lets all worktrees share one serial batch and cannot enter normal Git commits. Do not modify a team `.gitignore` merely to hide personal runtime state.
