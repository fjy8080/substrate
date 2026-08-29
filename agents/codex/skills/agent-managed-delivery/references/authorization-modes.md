# Authorization modes

## SUPERVISED

Use when the user remains available and wants decision points.

Required user actions:

1. Confirm that the task was claimed.
2. After implementation, self-test, documentation audit, and task report, approve creation of the exact-HEAD PR.
3. After required CI and an exact-HEAD `APPROVED_FOR_MERGE_BY_COMMENT`, approve merge of that PR and HEAD.

An approval is scoped to the recorded repository, task, action, and current HEAD. A new HEAD invalidates it. Never treat general encouragement such as “continue” as merge approval unless the action and scope are clear.

For PR creation, the first approved publication binds the task to a persistent PR identity. Later commits may update that same PR without consuming a new `create-pr` approval, but every new HEAD must still pass the exact-HEAD scope, test, CI, review, and merge gates. Replacing the PR with a different PR number requires fresh authorization.

## DELEGATED_BATCH

Use only after an explicit up-front grant. Record:

- repository identity and local root;
- remote and base branch;
- exact already-claimed task IDs;
- permission to create PRs and permission to merge after gates; both must be explicit for this offline mode;
- authorization evidence or the user's quoted instruction;
- exclusions and revocation, if any.

In this mode, still generate a complete task report and preserve it as evidence. Do not pause merely for PR or merge approval when those permissions were granted. All technical gates remain unchanged.

The grant does not cover:

- tasks absent from the list;
- another repository or base branch;
- predecessor or successor WBS tasks, adjacent deliverables, or any expansion of the approved task's ownership boundary;
- production deployment, release Go/No-Go, publishing, billing, secrets rotation, destructive data operations, or major architecture/compliance decisions;
- bypassing CI, review, exact-HEAD, documentation, or memory gates.

If the grant is ambiguous, missing a permission, revoked, or conflicts with repository rules, fall back to `SUPERVISED` for that action and ask the user.

Delegated authorization never permits the agent to redesign the WBS or silently broaden a task because a review finding appears important. When a finding exposes a predecessor defect, an unmerged dependency, or a WBS ambiguity that prevents safe continuation, enter `SCOPE_BLOCKED`. Only an explicit user decision may revise the scope contract through `scope-change`.

## Mode changes

- `SUPERVISED → DELEGATED_BATCH` requires a new explicit scoped grant.
- `DELEGATED_BATCH → SUPERVISED` may happen at the user's request or when scope becomes invalid.
- Preserve task evidence when switching; do not reuse approvals across changed HEADs.
