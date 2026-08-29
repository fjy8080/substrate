# Ordinary PR comment protocol

Use ordinary PR comments, not formal Approve or Request Changes, when the same GitHub identity is used by Developer and Reviewer contexts.

Allowed published review verdicts:

- `CHANGES_REQUIRED_BY_COMMENT`
- `APPROVED_FOR_MERGE_BY_COMMENT`

## Triage before publication

The Main agent must apply the round-aware evidence rule below and classify every published Reviewer
observation before a verdict. A Reviewer finding is evidence to investigate, not authority to enlarge
the current task.

Every finding must have two independent labels: a WBS ownership category and a severity. Use `P0`
for catastrophic security/compliance, irreversible data loss, or broad production failure; `P1` for a
reproducible core correctness/security/contract defect that blocks the current WBS acceptance;
`P2` for bounded impact that does not block core acceptance; `P3` for minor robustness,
maintainability, test, or documentation impact; and `P4` for style/preference/optional optimization.
Use `NA` only when no live defect impact remains, such as `INVALID` or `ALREADY_FIXED`. Never
inflate severity to keep a late review loop open.

The controller accepts `NA` only for `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, and `INVALID`, and those
categories must use `NA`. All other categories require P0-P4. `HARDENING_SUGGESTION` cannot be
P0/P1. A P0/P1 `FUTURE_WBS_GAP` is a scope blocker because the future-task boundary conflicts with
safe current acceptance; it is never a current Developer instruction.

Classification requires a direct link to the locked scope manifest: owned output, acceptance
criterion, required test, or regression introduced by the current diff. In review rounds 1-3, every
confirmed `IN_SCOPE_DEFECT` contributes to the blocking count. From round 4 onward, only
`P0/P1 + IN_SCOPE_DEFECT` contributes and may be sent to Developer; observed P2-P4 entries are
published only as deferred non-blocking observations. Do not proactively search for or fully expand
P2-P4 investigations in late rounds; perform only bounded verification needed to avoid mislabeling
their severity or ownership. The round counter is cumulative for the same
task/PR and cannot reset after a new HEAD, Reviewer, rebase, or scope revision.

Use these non-current-task categories explicitly:

- `PREDECESSOR_DEFECT`: required predecessor behavior is defective;
- `UNMERGED_DEPENDENCY`: expected behavior exists only on an unmerged branch/PR;
- `FUTURE_WBS_GAP`: the behavior belongs to a named later WBS task;
- `WBS_AMBIGUITY`: the WBS does not establish an unambiguous owner;
- `HARDENING_SUGGESTION`: beneficial improvement not required by current acceptance;
- `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `INVALID`: no actionable current defect remains.

`PREDECESSOR_DEFECT`, `UNMERGED_DEPENDENCY`, and `WBS_AMBIGUITY` are scope blockers in rounds
1-3, and remain blockers at P0/P1 from round 4 onward. Do not ask Developer to absorb them. Enter
`SCOPE_BLOCKED`, give the user evidence and bounded choices, and wait for a decision. A P2-P4
late-round scope observation is deferred; if a WBS ambiguity genuinely makes current acceptance
impossible, classify its real impact as P0/P1 and stop. `HARDENING_SUGGESTION` is always
non-blocking. `FUTURE_WBS_GAP` is non-blocking at P2-P4; at P0/P1, pause for a WBS/dependency
decision in every round.

## Required review body

Every published review comment must contain:

1. task ID, scope revision, review round, and full reviewed HEAD SHA;
2. exact-HEAD CI and documentation results;
3. exact-HEAD PR body metadata result (`PASS` or evidence-backed `NOT_REQUIRED`);
4. scope-audit evidence, including changed paths/capabilities and adjacent WBS ownership;
5. each reproduced finding with category, severity, and scope basis;
6. the active blocking threshold and count of severity-eligible `IN_SCOPE_DEFECT` findings;
7. deferred observations, including late-round P2-P4 current-scope defects, separated from fixes;
8. for round 2 and later, the delta from the prior round and regression surface examined;
9. for round 4 and later, an explicit statement that the review focused on P0/P1 and did not dispatch
   P2-P4 findings for repair.

End with a machine-readable block:

```text
<!-- agent-review
schema: 3
verdict: APPROVED_FOR_MERGE_BY_COMMENT
task_id: TASK-ID
review_round: 2
reviewed_head_sha: FULL-SHA
scope_revision: 1
blocking_findings: 0
in_scope_blocking_findings: 0
blocking_severities: [P0, P1]
deferred_non_blocking_findings: 0
deferred_scope_findings: 0
deferred_scope_finding_ids: []
scope_blocking_findings: 0
predecessor_defects: 0
unmerged_dependencies: 0
future_wbs_gaps: 0
wbs_ambiguities: 0
hardening_suggestions: 0
pr_metadata: PASS|NOT_REQUIRED
-->
```

For rounds 1-3, `blocking_severities` is `[P0, P1, P2, P3, P4]`; from round 4 onward it is
`[P0, P1]`. For `CHANGES_REQUIRED_BY_COMMENT`, `blocking_findings` and
`in_scope_blocking_findings` must be equal and greater than zero. For
`APPROVED_FOR_MERGE_BY_COMMENT`, both must be zero even when deferred P2-P4 observations exist.
Severity-eligible scope blockers must be zero for either published verdict.
Total category counts may still include late-round P2-P4 predecessor/dependency/WBS observations;
list them in `deferred_scope_finding_ids` rather than falsely reporting those categories as absent.

For a changes-required verdict, persist the exact eligible Finding IDs as the repair whitelist. A
later fix report must match that whitelist exactly and must not include deferred findings.

Every push, rebase, update branch, or conflict resolution invalidates the comment and its triage. Never claim that a same-account comment proves independent human identity.

An approved review is a technical gate, not a new authorization grant. In `SUPERVISED`, wait for the user's merge approval. In `DELEGATED_BATCH`, rely only on the recorded batch-level merge permission. Neither mode authorizes WBS redesign or scope expansion.
