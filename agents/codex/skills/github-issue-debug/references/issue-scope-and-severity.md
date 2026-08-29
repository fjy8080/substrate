# Issue repair severity and approval-boundary protocol

## Keep four decisions separate

For each Issue record:

1. truth classification (`CONFIRMED`, `ACTIONABLE_REQUIREMENT`, and so on);
2. severity (`P0`-`P4` for a proven defect, `NA` for a pure requirement or unsupported claim);
3. task ownership (`CURRENT_ISSUE`, `PREDECESSOR_TASK`, `UNMERGED_DEPENDENCY`,
   `FUTURE_TASK`, or `AMBIGUOUS_OWNER`);
4. contract impact (`NONE`, `IMPLEMENT_EXISTING`, or `CHANGE_REQUIRES_DECISION`).
5. execution disposition (`READY_TO_PLAN`, `EXTERNAL_BLOCKED`, `DUPLICATE_OWNER`,
   `ACTIVE_WORK_CONFLICT`, `DEPENDENCY_WAIT`, or `NO_ACTION`).

None substitutes for another. Severity does not prove truth or ownership, and a contract reference
does not import the whole contract into the Issue. For example, active work may yield
`truth=CONFIRMED`, `severity=P0`, `disposition=ACTIVE_WORK_CONFLICT`; the conflict must not erase the
confirmed impact.

## Severity definitions

| Severity | Meaning |
|---|---|
| `P0` | Catastrophic security/compliance impact, irreversible data loss, or broad production outage |
| `P1` | Reproducible core correctness, security, contract, migration, or compatibility defect blocking critical acceptance or causing severe regression |
| `P2` | Real bounded-impact defect with a workaround or no impact on core acceptance |
| `P3` | Minor robustness, maintainability, test, or documentation defect |
| `P4` | Style, wording, preference, or optional optimization |

## Freeze the approved manifest

The plan shown to the user must bind repository/Issue, evidence snapshot, remote `develop` SHA, root
cause, owned WBS/task, in-scope and out-of-scope capabilities, expected/allowed paths, contract
fingerprint and impact, dependencies/conflicts, validation, branch, and PR target. Implementation may
move within this manifest as code details require, but cannot change its owned behavior.

Record each contract fingerprint as `repository-relative path + Git blob SHA (or stable section
hash) + contract symbol/section + ADR/decision ID when present`. Compare every component on refresh.
`CHANGE_REQUIRES_DECISION` is never writable under ordinary plan approval: first obtain and record
the formal project decision, then refresh and present a replacement `IMPLEMENT_EXISTING` plan.

Before each branch creation, commit/push, and PR creation, compare live state and the complete delta
to the manifest by paths and capabilities. Stop and request renewed approval when:

- another Issue/WBS/PR owns the behavior;
- an unmerged dependency would need to be imported;
- the fix requires a new architecture or contract decision;
- changed paths or behavior materially exceed the approved inclusions;
- WBS ownership is ambiguous or the approved root cause is no longer true.

A newly discovered defect is reported as a separate candidate Issue or owner mapping; it is not
fixed opportunistically. Later PR review feedback belongs to `$github-pr-fix`, which must independently
enforce the same PR boundary and review-round convergence rules.
