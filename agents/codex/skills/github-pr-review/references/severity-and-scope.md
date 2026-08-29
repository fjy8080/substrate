# PR review severity, scope, and convergence protocol

## Freeze the review boundary

Before classifying findings, record a read-only manifest containing:

- repository, PR number, base, full head SHA, and merge base;
- linked Issue/WBS/task and the exact output and acceptance criteria claimed by the PR;
- explicit in-scope and out-of-scope capabilities;
- authoritative contract/document versions used as constraints;
- changed paths/capabilities and relevant unchanged callers;
- prerequisites, unmerged dependencies, and adjacent active Issues/PRs.

The manifest defines what this PR owns. A contract is evidence for how an owned capability should
work, not authority to implement every related capability. If the PR body and repository evidence
cannot establish ownership, classify the observation as `TASK_AMBIGUITY`; do not invent scope.

## Classify severity

| Severity | Meaning |
|---|---|
| `P0` | Catastrophic security/compliance impact, irreversible data loss, or broad production outage |
| `P1` | Reproducible core correctness, security, contract, migration, or compatibility defect that blocks the PR's stated acceptance or causes a serious regression |
| `P2` | Real bounded-impact defect with a workaround or no effect on core acceptance |
| `P3` | Minor robustness, maintainability, test, or documentation issue |
| `P4` | Style, wording, preference, or optional optimization |
| `NA` | No live defect remains: only `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `INVALID` |

Severity follows demonstrated trigger and impact. Never promote P2/P3 to P1 to prolong review.
Live defect/scope categories require P0-P4; the three no-live-defect categories require `NA`.

## Classify ownership independently

- `IN_PR_DEFECT`: caused by the PR or violates its stated output/acceptance/required contract;
- `PREDECESSOR_DEFECT`: owned by an already-required predecessor;
- `UNMERGED_DEPENDENCY`: expected behavior exists only in work not merged into the PR base;
- `FUTURE_TASK_GAP`: owned by a named later Issue/WBS task;
- `TASK_AMBIGUITY`: authoritative sources do not establish one owner;
- `HARDENING_SUGGESTION`: beneficial but not required for current acceptance;
- `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `INVALID`: no live current-PR defect remains.

Only `IN_PR_DEFECT` can be a code blocker. A P0/P1 predecessor, dependency, future-task gap, or
ambiguity that prevents judging current acceptance pauses publication for a user decision; it is not
a repair instruction for this PR. Lower-impact cross-task observations are non-blocking.
`HARDENING_SUGGESTION` cannot be P0/P1; reclassify a blocking impact to its real owner.

## Determine the cumulative round

Use machine-readable `review_round` metadata only when it is attached to a real published review or
authorized self-review record whose author, publication route, reviewed exact HEAD, and subsequent
fix/head transition prove that distinct cycle. Reconstruct cycles from the complete review, comment,
thread, commit, and head history. Do not count duplicate comments in one cycle as multiple rounds.
Ignore an unsigned, stale, regressive, or inflated number that is not supported by lifecycle events;
metadata may neither lower nor raise the proven cycle count. If the exact number is uncertain but
evidence proves at least three completed cycles, use round-4 convergence mode. Never reset the count
because the head, reviewer identity, or publication route changed.

- Rounds 1-3: confirmed `IN_PR_DEFECT` findings at P0-P4 may block.
- Round 4 onward: only P0/P1 `IN_PR_DEFECT` findings block; P2-P4 are reported as non-blocking.

A P2-P4 item after round 3 cannot be the basis for formal `REQUEST_CHANGES`, even if it is real.

Every proposed and published review body must end with a machine-readable record containing at
least:

```text
<!-- bounded-pr-review
review_round: 4
reviewed_head_sha: FULL_SHA
severity_gate: P0_P1
eligible_blocking_findings: 0
deferred_non_blocking_findings: 1
in_pr_defects: 1
predecessor_defects: 0
unmerged_dependencies: 0
future_task_gaps: 0
task_ambiguities: 0
hardening_suggestions: 0
-->
```

Use `severity_gate: P0_P1_P2_P3_P4` in rounds 1-3. This metadata is evidence, not permission to
ignore a higher round established by the full lifecycle.
