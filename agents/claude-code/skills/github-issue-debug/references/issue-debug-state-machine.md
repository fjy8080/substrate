# Issue debug and isolated delivery state machine

## Per-request state flow

```text
ISSUES_REQUESTED
  -> EVIDENCE_SNAPSHOTTED
  -> ISSUES_TRIAGED
  -> PLANS_DRAFTED
  -> AWAITING_PLAN_APPROVAL
       -> PLANS_DRAFTED             (user changes scope/order)
       -> ISSUE_QUEUE_READY          (one or more exact plans approved)

ISSUE_QUEUE_READY
  -> REFRESHING_ISSUE_1
       -> AWAITING_PLAN_APPROVAL     (material delta/conflict)
       -> ISOLATING_ISSUE_1
       -> DEVELOPING_ISSUE_1
       -> VALIDATING_ISSUE_1
       -> REPORTING_ISSUE_1
       -> PR_CREATING_ISSUE_1
       -> PR_METADATA_SYNCING_ISSUE_1
       -> PR_VERIFIED_ISSUE_1
  -> REFRESHING_ISSUE_2
       -> ...
  -> QUEUE_COMPLETED
```

`AWAITING_PLAN_APPROVAL` is the only transition from investigation to writes. Each Issue has its own
state sequence; evidence, branches, commits, tests, and PRs cannot be reused as another Issue's gate.
`PR_METADATA_SYNCING` is an internal PR-publication substate: it may update only validator-required
dynamic fields and cannot change approved narrative scope.

`CHANGE_REQUIRES_DECISION` cannot enter `ISSUE_QUEUE_READY`. Ordinary plan approval is insufficient:
the project-required decision-maker must approve the contract/WBS decision first. Record that
decision, refresh all live evidence, convert the impact to `IMPLEMENT_EXISTING`, and present a new
repair plan for approval.

## Truth classifications and execution dispositions

| Truth | Meaning | Default action |
|---|---|---|
| `CONFIRMED` | Current `develop`/code reproduces or proves the defect | Prepare repair plan |
| `PARTIALLY_CONFIRMED` | Only part of the Issue remains true | Correct scope and request approval |
| `ACTIONABLE_REQUIREMENT` | The Issue is a valid change/task rather than a current defect | Prepare a scoped implementation plan when its prerequisites are ready |
| `ALREADY_FIXED` | Current remote `develop` already fixes it | Report evidence; no branch/PR |
| `NOT_REPRODUCIBLE` | Faithful reproduction does not fail | Report evidence; clarify before code |
| `INVALID` | Contradicts authoritative behavior or false premise | Do not modify code |
| `NEEDS_CLARIFICATION` | Cannot decide safely | Ask a focused question |

Record disposition independently so it cannot erase confirmed truth or severity:

| Disposition | Meaning/action |
|---|---|
| `READY_TO_PLAN` | Truth, ownership, dependency, and contract gates permit a plan |
| `EXTERNAL_BLOCKED` | Required environment, artifact, credential, owner decision, or prerequisite unavailable; do not create speculative work |
| `DUPLICATE_OWNER` | Another Issue owns the work; preserve truth/severity but do not compete |
| `ACTIVE_WORK_CONFLICT` | An open PR/branch/worktree owns overlapping work; coordinate or wait |
| `DEPENDENCY_WAIT` | Required work is unmerged; do not import it |
| `NO_ACTION` | Already fixed, invalid, or otherwise no code action |

## Approval binding

Approval is per Issue and binds to:

- repository and Issue number;
- Issue state/body/comments considered;
- root cause and scope/exclusions;
- dependency and conflict analysis;
- remote `develop` SHA presented as the planning baseline;
- proposed branch, validation, and PR target;
- severity and task/WBS ownership classification;
- execution disposition;
- authoritative contract fingerprint and declared contract impact;
- the approved path and capability inclusions/exclusions.

Normal advancement of unrelated PRs does not always invalidate approval. A delta is material when it
changes the relevant files/behavior, root cause, base compatibility, task ownership, or dependency
order; adds a new contract decision; or expands approved paths/capabilities. Record the comparison
either way.

## Required dynamic audits

Perform a live audit at four points:

1. before presenting the plan;
2. after approval and before branch/worktree creation;
3. before commit/push;
4. before PR creation.

At minimum inspect:

- all requested Issue comments/timeline/state;
- remote `develop` SHA;
- every open PR number, base, head branch, head SHA, fully paginated changed files, commits, formal
  reviews, conversation comments, and inline comments;
- PR bodies/titles linking the Issue;
- local/remote branch-name collisions;
- all live remote branch names and head SHAs, including branches without an open PR;
- all worktree paths and checked-out branches;
- dirty state in every visible worktree and dirty files in any worktree that might be reused;
- overlapping changed files/symbols for relevant PRs.

If a remote-head, worktree-status, or open-PR detail query is incomplete, the audit is incomplete.
Do not silently treat missing evidence as “no conflict.”

An open PR with no Issue link may still conflict by file or behavior. Search both linkage and diff.

## Isolation invariants

- Never commit on `develop`, `main`, or `master`.
- Never branch from stale local `develop`.
- Never place two Issues on one branch or PR.
- Never reuse a dirty or differently owned worktree.
- Never force-push or reset another branch.
- Never import an unmerged dependency silently.
- Never create a PR to a base other than `develop` under this Skill.
- Never merge the created PR.
- Never absorb a newly discovered adjacent defect into the current Issue branch; report it separately.
- Never change an authoritative contract unless the approved Issue plan explicitly owns that change
  and project decision rules permit it.

Use a unique explicit worktree path outside another active task's directory. Validate the resolved
path and branch before creating it. Preserve the worktree after PR handoff unless cleanup is
separately authorized.

## Multiple-Issue ordering

Default to serial execution. Before Issue N+1, rerun the complete snapshot because Issue N's PR and
other actors may have changed the conflict surface.

If Issue N+1 depends on Issue N:

- prefer waiting for Issue N's PR to merge into `develop`;
- then create Issue N+1 from the new remote `develop`;
- do not stack branches unless the user explicitly approves a stacked strategy after seeing its
  review and rebase consequences.

If two Issues are duplicates or require one inseparable change, report that conflict and request a
user decision. Do not violate the one-Issue/one-PR rule by assumption.

## PR handoff requirements

The Ready PR must include:

- base `develop` and the exact pushed head SHA;
- one Issue closing reference;
- root cause and correction summary;
- changed scope and explicit exclusions;
- validation commands/results;
- compatibility, risk, and rollback notes;
- current conflict/CI state;
- repository template fields.

Before CI handoff, inspect the live PR twice for a stable exact head/base/commit/file snapshot,
synchronize any repository-required dynamic body metadata, and re-read the body. Preserve all
non-metadata text. Record `PASS` with exact-head evidence, or `NOT_REQUIRED` with repository
template/workflow evidence. A new push or relevant base-statistics change invalidates this evidence.

Verify the PR through live GitHub after creation. PR creation is not merge authorization.
