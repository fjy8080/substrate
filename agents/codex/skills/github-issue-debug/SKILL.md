---
name: github-issue-debug
description: Investigate one or more GitHub Issue numbers against current code and live work, classify truth, severity, WBS ownership, and contract impact, then after explicit plan approval implement each locked Issue scope on its own isolated branch/worktree and develop PR. Use only when the user explicitly invokes `$github-issue-debug` or sends `修复issue` / `修复 issue` with one or more Issue numbers. Never infer this workflow from ordinary debugging or development requests.
---

# GitHub Issue Debug

## Separate investigation from implementation

Treat `修复issue #<number>...` as authorization to inspect Issues, code, and live repository state
and to propose plans. Do not edit code, create worktrees/branches, commit, push, or create PRs until
the user explicitly approves the presented repair plan.

Read the repository's `AGENTS.md`, Git/PR rules, issue templates, authoritative contracts, current
configuration, and memory. Repository rules may add stricter approval gates; never weaken them.

Read [issue-scope-and-severity.md](references/issue-scope-and-severity.md). Severity, truth, task
ownership, and approval are separate dimensions: a P0 claim is not automatically true or in scope,
and a confirmed issue does not authorize an adjacent WBS task or contract redesign.

## Capture complete current evidence

Run from the repository in scope, passing every requested Issue explicitly:

```bash
python3 <THIS-SKILL>/scripts/issue_evidence.py \
  --issue 12 --issue 34 --target-base develop
```

Read [issue-debug-state-machine.md](references/issue-debug-state-machine.md) before planning or
writing. Stop if the current repository does not match the user's scope, an Issue number resolves to
a PR, or the remote `develop` branch does not exist.

Require every relevant snapshot `completeness` flag to be true. In particular, a failed remote-head
query, unreadable worktree status, or incomplete open-PR files/reviews/comments/commits means the
parallel-work audit is incomplete: resolve the gap or stop and report it instead of presenting an
implementation-ready plan.

Snapshot schema 2 records capture start/end, verifies a repository-matching remote and target branch,
re-reads every requested Issue and every open PR around detail collection, and rechecks the final
open-Issue/open-PR inventories, labels, local worktrees, remote heads, and target branch. It fails
closed on command timeout or launch failure, malformed endpoint data, count mismatch, concurrent
movement, more than 40 open PRs, or PRs beyond the REST endpoints' provable file/commit limits; never
downgrade those errors to “no conflict.”

For every Issue:

1. Read its full body, comments, timeline, labels, owner/state, linked work, and acceptance evidence.
2. Inspect relevant code, tests, configuration, contracts, blame/history, and safe reproduction.
3. Check all open PRs, their exact heads/bases, related Issue references, active branches/worktrees,
   each worktree's dirty state, all live remote branch heads, and other work touching the same files
   or behavior.
4. Record truth as `CONFIRMED`, `PARTIALLY_CONFIRMED`, `ACTIONABLE_REQUIREMENT`,
   `ALREADY_FIXED`, `NOT_REPRODUCIBLE`, `INVALID`, or `NEEDS_CLARIFICATION`. Separately record
   execution disposition as `READY_TO_PLAN`, `EXTERNAL_BLOCKED`, `DUPLICATE_OWNER`,
   `ACTIVE_WORK_CONFLICT`, `DEPENDENCY_WAIT`, or `NO_ACTION`; a conflict never erases truth or severity.
5. Identify dependencies between the requested Issues and other open Issues/PRs. Never assume an
   unmerged PR is available on `develop`.
6. Assign confirmed defects `P0`-`P4`, classify task ownership, and fingerprint the authoritative
   contracts that constrain the fix. Requirements use `NA` severity unless they also document a
   proven current defect.

Do not trust Issue prose blindly. Confirm current behavior and ownership before proposing code.
Do not force a non-defect Issue into a defect repair. A valid requirement may have an implementation
plan; an externally blocked validation/coordination Issue must remain blocked until its named
condition is satisfied and must not receive a speculative repair branch.

## Present a per-Issue plan

For each independently actionable Issue, present:

- Issue URL/title and current classification;
- reproduced root cause or remaining uncertainty;
- exact scope and explicit exclusions;
- severity, task/WBS owner, contract impact (`NONE`, `IMPLEMENT_EXISTING`, or
  `CHANGE_REQUIRES_DECISION`), execution disposition, and the immutable approval manifest;
- expected files/contracts/tests;
- conflict analysis against every relevant open PR/branch/worktree;
- dependency/order constraints;
- proposed unique branch `fix/issue-<number>-<slug>`;
- captured remote `develop` SHA;
- validation commands;
- rollback point and risks;
- planned PR title/body, `develop` target, and repository-required dynamic body metadata contract.

For multiple Issues, provide a serial execution order. One Issue must map to one repair branch, one
worktree, one focused commit series, and one PR. Do not combine Issues even when convenient. If two
Issues cannot be separated safely, stop and ask the user rather than silently combining them.

State clearly that no implementation or GitHub mutation has occurred. Wait for explicit approval of
the plans. A question, partial edit, or approval of only one Issue authorizes only that Issue.

Ordinary repair-plan approval never authorizes `CHANGE_REQUIRES_DECISION`. First obtain the formal
contract/WBS decision from the role required by project rules, record its evidence, reclassify the
impact as `IMPLEMENT_EXISTING`, refresh repository/conflict evidence, and present a new implementation
plan for approval. Until then the Issue stays non-writable.

## Refresh before each repair

After approval and before starting each Issue, rerun the evidence script and fetch the selected
remote's current `develop`. Re-read the Issue and relevant PRs. Compare:

- Issue state/body/comments/assignment;
- remote `develop` SHA;
- open PRs and their heads/bases;
- branch/worktree ownership;
- overlapping files and newly merged or newly opened work.
- task/WBS ownership, contract fingerprint/impact, and approved path/capability boundaries.

If a material delta invalidates root cause, scope, order, or conflict analysis, do not start coding.
Show the delta and request plan approval again.

## Isolate and implement one Issue at a time

For each approved Issue:

1. Select the repository's verified push remote; do not assume it is named `origin`.
2. Fetch/prune it and verify the exact remote `develop` SHA.
3. Check that the proposed branch is absent from local refs, remote refs, open PRs, and all worktrees.
   Never overwrite, reset, or reuse another actor's branch without explicit direction.
4. Create a new dedicated worktree and `fix/issue-<number>-<slug>` branch directly from the latest
   remote `develop`. Never develop in the existing `develop` worktree or from stale local `develop`.
5. Implement only the approved Issue scope, add a regression test where practical, and run focused
   then repository-required validation. Compare both paths and capabilities with the approved
   manifest before every commit. A newly found defect is not silently part of this Issue.
6. Before commit/push, refresh relevant open PR heads and inspect the complete diff for scope and
   overlap. Reconcile safe non-conflicting changes; stop for user direction when work ownership or
   architecture would change, or when the fix would revise rather than implement the approved
   contract.
7. Create focused commits, push normally without force, and verify the remote branch SHA.

Never merge another unmerged Issue branch into the repair branch to “get dependencies”. If a later
Issue requires an earlier unmerged PR, wait for `develop` to receive it or ask the user to authorize
an explicit stacked strategy; the default remains independent PRs from `develop`.

## Report and create the PR

Report the exact branch/head, changed files, evidence, tests, current CI/PR conflicts, compatibility,
and rollback point. Then create a Ready PR targeting `develop` with the repository template and an
appropriate closing reference such as `Fixes #<number>`.

The user's approved plan normally authorizes the planned commit, normal push, and PR creation. If
repository instructions require a post-implementation exact-HEAD approval before creating the PR,
pause at the report and obtain it.

Immediately before PR creation, refresh the Issue, remote `develop`, and open PR list again. Verify
the created PR's repository, base=`develop`, head branch/SHA, body, linked Issue, and draft status.

Treat repository-required mechanical PR body metadata as part of the approved PR-publication
transaction, not as permission to rewrite the narrative. Inspect the template, workflow, and
validator before creation. If the repository uses the hidden `base/commits/files` contract, run this
immediately after GitHub exposes the new PR:

```bash
python3 <THIS-SKILL>/scripts/sync_pr_metadata.py \
  --repo OWNER/REPO --pr NUMBER --expected-head FULL_SHA \
  --required-base develop --apply
```

Require `UPDATED` or `IN_SYNC`, then re-read the PR. The synchronization must preserve all
non-metadata body content and bind the live base, commit count, changed-file count, and body hash to
the exact head before CI is treated as valid handoff evidence. If the repository uses another
schema, satisfy its validator-defined equivalent; if none exists, record `NOT_REQUIRED` with the
inspection evidence. A synchronization failure leaves `PR_CREATING` incomplete.

Every later authorized push to the same Issue PR repeats this gate before checking CI. Never merge
the PR, resolve the Issue manually, or start unapproved follow-up work.

If that PR later receives review feedback, use `$github-pr-fix` under its own trigger and convergence
rules. Do not silently turn review comments into an expansion of the approved Issue plan.

Finish one Issue's PR handoff before starting the next unless the user explicitly approves safe
parallel execution and every worktree remains isolated.
