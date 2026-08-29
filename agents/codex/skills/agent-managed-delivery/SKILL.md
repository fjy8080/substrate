---
name: agent-managed-delivery
description: Run or resume the user's scope-locked multi-agent software delivery workflow across Git repositories, with exact-HEAD gates, WBS-aware finding triage, and P0/P1-only convergence after three review/fix rounds. Use only when the user explicitly invokes `$agent-managed-delivery` or explicitly asks to use the “Agent Managed Delivery” workflow; never infer it from an ordinary development, review, PR, CI, or delivery request.
---

# Agent Managed Delivery

## Start safely

1. Read the repository's `AGENTS.md`, `README`, real configuration, authoritative documents, task source, and local memory before acting.
2. Inspect Git status, remotes, base branch, open PRs, CI, task dependencies, and existing runtime. Treat repository rules as higher-priority project adapters.
3. Select exactly one authorization mode from the user's explicit instruction. Never infer offline delegation from absence or silence.
4. Use `scripts/workflowctl.py` for durable local state. It stores one repository-wide batch in the private Git common directory so all worktrees can resume it without creating tracked files. Read [commands.md](references/commands.md) for initialization and evidence commands.
5. Read [authorization-modes.md](references/authorization-modes.md) before initializing a batch and the complete Chinese [state-machine.md](references/state-machine.md) before advancing a task.

## Choose authorization mode

- `SUPERVISED`: generate and present the task report, then wait for user approval before creating the PR. After exact-HEAD review approval, wait again for user approval before merging.
- `DELEGATED_BATCH`: require one explicit up-front grant naming the repository, base branch, exact task IDs, and whether PR creation and merge are delegated. Generate every task report, but do not pause at delegated approval points. Never extend the grant to another task, repository, base branch, production deployment, release Go/No-Go, destructive recovery, or major architecture/compliance decision.

Use one state machine for both modes. Only authorization gates differ. A user may revoke delegation at any time; switch to supervised behavior immediately and preserve completed evidence.

## Orchestrate roles

- Main Agent owns state, the immutable task-scope interpretation, review-finding reproduction and classification, authorization checks, external writes, and final truth claims. It may direct Developer to perform the already-authorized PR creation/push and the same-PR mechanical metadata synchronization, but must verify the live result before advancing state.
- Task Scout is read-only and recommends tasks; it never claims for the user.
- Explorer is read-only and maps code, contracts, tests, and risks.
- Developer is the only code writer for the task worktree.
- Knowledge Keeper writes only after Developer stops, and closes documentation and memory.
- Reviewer uses a fresh read-only context each round and reviews the complete exact-HEAD diff against the recorded WBS scope. It may report cross-task observations but cannot promote them to current-task blockers.
- Utility performs deterministic read-only extraction and checks.

Prefer the personal custom agents installed in `~/.codex/agents/`. Keep business tasks serial. Parallelize only independent read-only work. Never run Developer and Knowledge Keeper as concurrent writers in one worktree. Read [subagent-scheduling.md](references/subagent-scheduling.md) whenever subagents are available.

## Execute the workflow

Follow this public state machine exactly:

`CANDIDATE → CLAIMED → EXPLORING → DEVELOPING → SELF_TESTING → IMPLEMENTATION_READY_FOR_DOCS → DOCUMENTING → PR_CREATING → CI_PENDING → REVIEW_REQUESTED → REVIEWING → MERGE_READY → MERGING → MERGED → VERIFYING_DEVELOP → POST_MERGE_MEMORY → COMPLETED`

Use `FIXING_CI`, `FIXING_REVIEW`, user-decision `SCOPE_BLOCKED`, and evidence-backed `SERIOUSLY_BLOCKED` as defined in [state-machine.md](references/state-machine.md). Do not add public states for repository-specific checks; enforce them as internal gates in the closest source state and report them.

For each task:

1. Confirm the user claimed it, or that it is named in an explicit delegated batch of already-claimed tasks.
2. Create a clean task branch/worktree from the repository's current base branch.
3. Explore authoritative sources, adjacent WBS tasks, dependency status, and project-specific gates. Record a scope manifest before development: WBS source, independent output, acceptance, tests, authoritative inputs, inclusions, exclusions, dependencies, and allowed paths. Treat WBS output/acceptance as what to build and authoritative documents as how to build it.
4. Run `scope-check` on every new HEAD before self-test. Implement only within the active scope revision. Bind validation evidence to the exact HEAD; invalidate it after every new commit, rebase, update-branch, or conflict resolution without invalidating or silently expanding the scope manifest.
5. Stop Developer writes, then audit and update all affected documentation. Generate a non-empty task report in both modes.
6. Pass the create-PR authorization gate for the selected mode. Use the repository's existing PR template; do not create a replacement unless the repository has none and the user requests one. Inspect repository-required dynamic PR body metadata, synchronize it to the live exact HEAD immediately after PR creation or every push, and verify it before leaving `PR_CREATING`.
7. Wait for all path-applicable required CI only after the PR metadata gate is `PASS` or evidence-backed `NOT_REQUIRED`. Repair failures without starting the next business task.
8. Request a fresh Reviewer context. In rounds 1-3, independently reproduce every candidate finding. From round 4 onward, proactively investigate only potential P0/P1; if a P2-P4 item is incidentally observed, record enough evidence to justify its severity and WBS ownership but do not expand the search or repair scope around it. Assign P0-P4 to live observations and `NA` only when no live defect remains, then classify with `review-triage`; a true observation is not automatically a current-task blocker. Read [comment-protocol.md](references/comment-protocol.md), then post the classified ordinary PR comment; never impersonate formal human approval.
9. Keep the review-round counter monotonic for the same task/PR even after a new HEAD, Reviewer context, or scope revision. In rounds 1-3, send all confirmed `IN_SCOPE_DEFECT` entries to Developer. From round 4 onward, review and repair only `P0/P1 + IN_SCOPE_DEFECT`; retain any observed P2-P4 item as a non-blocking comment and do not dispatch it for code changes. Persist the eligible Finding IDs as an exact repair whitelist. The whitelist remains active until the next published Review: every intervening new HEAD, even after leaving `FIXING_REVIEW`, requires `review-fix-record` to match that whitelist and enumerate changed capabilities before `scope-check PASS`; preserve both authorization and repair history across HEAD changes. Then self-test, re-audit docs, refresh the same PR, synchronize and read back its exact-HEAD metadata, rerun CI, and review the full new HEAD for P0/P1 regressions. Never inflate severity to evade this convergence rule. Run an enhanced scope audit on later-round new categories, new modules/shared abstractions, material diff growth, or neighboring-task findings.
10. Treat severity-eligible `PREDECESSOR_DEFECT`, `UNMERGED_DEPENDENCY`, and `WBS_AMBIGUITY` as scope blockers, not repair instructions. In rounds 1-3 all severities are eligible; from round 4 onward only P0/P1 are. Enter `SCOPE_BLOCKED`, preserve evidence, present options and required user action, and do not redesign WBS or continue coding. Keep late-round P2-P4 scope observations non-blocking. Resume only through an explicitly user-approved `scope-change`.
11. Pass the merge authorization gate for the selected mode, protect the reviewed HEAD in the merge command, and never use admin bypass.
12. Verify the merge commit is in the remote base branch. Then update project memory, emit a non-empty durable summary, run a secrets check, and complete the task.
13. Start the next claimed task only after the current task is `COMPLETED` or genuinely `SERIOUSLY_BLOCKED`. `SCOPE_BLOCKED` remains the active task and requires a user decision.

Read [project-adaptation.md](references/project-adaptation.md) for repository-specific gates and [comment-protocol.md](references/comment-protocol.md) for PR comments. Reuse templates from `assets/templates/`.

## Report accurately

State the current mode, task, gate, exact HEAD, actual validation, and remaining authority. Never treat local tests as remote CI, a drafted comment as a published review, a merge command as verified integration, or a delegated development grant as production/release authority.
