# PR repair scope, severity, and convergence protocol

## Freeze repair authority

Before changing code, record a repair manifest containing the repository/PR, base and captured head,
linked Issue/WBS/task, stated output and acceptance, explicit exclusions, authoritative contract
versions, allowed paths/capabilities, dependencies, and relevant active work. Each feedback item must
map to this manifest. Reviewer prose cannot expand it.

Use these scope classifications:

- `IN_PR_SCOPE`: the PR introduced the regression or the item violates the PR's stated acceptance;
- `PREDECESSOR_DEFECT`: another merged predecessor owns the defect;
- `UNMERGED_DEPENDENCY`: the requested behavior depends on work absent from the PR base;
- `FUTURE_TASK_GAP`: a named later Issue/WBS task owns it;
- `TASK_AMBIGUITY`: authoritative sources do not identify one owner;
- `HARDENING_SUGGESTION`: useful but not required for current acceptance.

Only `IN_PR_SCOPE` may enter the repair queue. For the other categories, preserve evidence and ask
for a user decision only when the condition blocks P0/P1 acceptance. Never redesign WBS or revise a
contract merely to satisfy feedback. A contract correction already stated by the PR is in scope; a
new contract decision is not.

`HARDENING_SUGGESTION` cannot be P0/P1; reclassify blocking impact to its real owner. A P0/P1
`FUTURE_TASK_GAP` pauses for a WBS/dependency decision rather than entering this PR's code queue.

## Assign severity

| Severity | Meaning |
|---|---|
| `P0` | Catastrophic security/compliance impact, irreversible data loss, or broad production outage |
| `P1` | Reproducible core correctness, security, contract, migration, or compatibility defect blocking stated PR acceptance or causing severe regression |
| `P2` | Real but bounded impact, workaround available, or no effect on core acceptance |
| `P3` | Minor robustness, maintainability, test, or documentation issue |
| `P4` | Style, wording, preference, or optional optimization |
| `NA` | No live defect remains after `ALREADY_FIXED`, `NOT_REPRODUCIBLE`, or `INVALID` triage |

Use the demonstrated trigger and impact. Never inflate severity to keep a repair cycle active.

## Reconstruct the cumulative round

Accept explicit `review_round` metadata only when it is attached to a real review/self-review record
whose author, route, exact reviewed HEAD, and subsequent fix/head lifecycle prove that distinct cycle.
Otherwise reconstruct cycles from the complete formal-review, conversation, thread, commit, and head
lifecycle. Duplicate sources in one cycle count once. A new head, reviewer, or route does not reset
the count. Ignore stale, regressive, or inflated metadata that is not lifecycle-supported; it may
neither lower nor raise the proven cycle count. If the exact number is uncertain but at least three
completed cycles are proven, use round-4 mode.

The code queue is:

```text
ACTIVE_FEEDBACK
  AND CONFIRMED
  AND IN_PR_SCOPE
  AND (round <= 3 OR severity IN {P0, P1})
```

P2-P4 after round 3 remains in the ledger and proposed response as a non-blocking observation. It
must not cause a commit, push, CI cycle, or new review request.

## Recheck before handoff

Before each commit and push, compare the complete delta to the frozen manifest by both paths and
capabilities. Stop when a fix requires another task, an unmerged dependency, a new architecture or
contract decision, or materially broader files/behavior. User approval of replies is not scope-change
approval.
