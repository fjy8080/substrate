# Issue review triage dimensions

## Keep five decisions separate

For each Issue record all five dimensions. None substitutes for another: severity does not prove
truth, ownership does not set severity, and a contract reference does not import the whole contract
into this Issue.

1. **truth** — does current `origin/develop` actually exhibit the reported defect?
2. **severity** — if the defect is real, what is its impact?
3. **task ownership** — which WBS/PR/actor owns the behavior the Issue concerns?
4. **contract impact** — does the fix need a new CHG/ADR decision, or does it implement an existing one?
5. **review disposition** — what is this skill's recommended action for the Issue right now?

## Truth classifications

| Truth | Meaning | Default review disposition |
|---|---|---|
| `CONFIRMED` | Current `origin/develop` reproduces or proves the defect | `READY_TO_FEEDBACK` |
| `PARTIALLY_CONFIRMED` | Only part of the Issue remains true | `READY_TO_FEEDBACK` with corrected scope |
| `ACTIONABLE_REQUIREMENT` | The Issue is a valid change/task rather than a current defect | `READY_TO_FEEDBACK` as a requirement, not a defect |
| `ALREADY_FIXED` | Current `origin/develop` or an open PR already fixes it | `ALREADY_FIXED`; propose closing with evidence |
| `NOT_REPRODUCIBLE` | Faithful reproduction does not fail | `NEEDS_REPRO`; ask reporter for steps/data/version |
| `INVALID` | Contradicts authoritative behavior, contract, or false premise | `INVALID_AS_REPORTED`; propose closing |
| `NEEDS_CLARIFICATION` | Cannot decide safely from the report | `NEEDS_REPRO` or `NEEDS_DECISION` |

Do not trust Issue prose blindly. A P0 label on an Issue is a reporter claim, not a confirmed P0
defect. Confirm current behavior against the exact `origin/develop` SHA before assigning truth.

## Severity definitions

| Severity | Meaning |
|---|---|
| `P0` | Catastrophic security/compliance impact, irreversible data loss, or broad production outage |
| `P1` | Reproducible core correctness, security, contract, migration, or compatibility defect blocking critical acceptance or causing severe regression |
| `P2` | Real bounded-impact defect with a workaround or no impact on core acceptance |
| `P3` | Minor robustness, maintainability, test, or documentation defect |
| `P4` | Style, wording, preference, or optional optimization |
| `NA` | No proven current defect: pure requirement, `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `INVALID` |

Severity follows demonstrated trigger and impact against current `origin/develop`, never the
reporter's label. Never promote P2/P3 to P1 to make the Issue sound urgent. If the Issue reports a
future risk, it is `ACTIONABLE_REQUIREMENT` with `NA` severity, not a P0 defect.

## Task ownership

| Ownership | Meaning |
|---|---|
| `CURRENT_ISSUE` | No other WBS/PR owns the behavior; this Issue is the canonical owner |
| `PREDECESSOR_TASK` | A required earlier WBS/PR is the actual owner; this Issue inherits the gap |
| `UNMERGED_DEPENDENCY` | The fix exists only in unmerged work; wait for `develop` to receive it |
| `FUTURE_TASK` | A named later WBS/Issue owns the behavior by design |
| `AMBIGUOUS_OWNER` | Authoritative sources do not establish one owner; do not speculate |

An Issue with a duplicate root cause and scope as another Issue is `DUPLICATE` (cite the canonical
Issue). Partial overlap is `RELATED`, never `DUPLICATE`. When the Issue claims a defect that belongs
to a future planned task, record `FUTURE_TASK` and the WBS pointer; do not let the reporter's
urgency override the plan.

## Contract impact

| Impact | Meaning |
|---|---|
| `NONE` | No contract reference applies; pure runtime/UX defect |
| `IMPLEMENT_EXISTING` | The fix implements an existing authoritative contract as written |
| `CHANGE_REQUIRES_DECISION` | The fix requires a new CHG/ADR decision by the project-required role |

`CHANGE_REQUIRES_DECISION` Issues stay non-actionable under this skill. Record the contract
fingerprint (`repository-relative path + Git blob SHA + contract symbol/section + ADR/decision ID`)
and recommend that the reporter or maintainer open the CHG/ADR decision first. This skill never
pre-approves a contract change.

## Review disposition (this skill's action axis)

| Disposition | Action |
|---|---|
| `READY_TO_FEEDBACK` | Publish triage feedback to the reporter (truth/severity/ownership/contract) |
| `EXTERNAL_BLOCKED` | Needs environment, credential, artifact, or external owner; no speculative comment |
| `DUPLICATE` | Same root cause and scope as another Issue; comment with canonical pointer; propose closing or cross-linking |
| `RELATED` | Overlaps another Issue but not identical; cross-link only |
| `ALREADY_FIXED` | Current `develop`/PR fixes it; propose closing with the fixing commit/PR |
| `INVALID_AS_REPORTED` | Authoritative behavior contradicts the claim; propose closing with contract reference |
| `NEEDS_REPRO` | Missing reproduction steps/data/version/role/device; ask the reporter |
| `NEEDS_DECISION` | Requires CHG/ADR decision before any action; do not speculate |

## Cross-Issue relationship graph

When more than one Issue is requested, build the relationship graph before reporting:

- `DUPLICATE`: identical confirmed root cause **and** identical owned scope. Cite the canonical
  Issue (lowest number, or the one with the most complete report).
- `RELATED`: overlapping files, behavior, or capability, but different root cause or different
  owned scope. Cross-link; do not merge.
- `DEPENDENCY`: Issue A must be resolved before Issue B can be reproduced or fixed. Record
  direction.
- `INDEPENDENT`: no relationship.

A cluster of `DUPLICATE` Issues can share a single canonical triage paragraph, but each Issue
thread still receives its own published comment pointing to the canonical Issue. This skill never
silently closes a duplicate; closure requires explicit user approval per Issue.

## Severity-vs-truth interaction

- A `CONFIRMED` Issue with `P0`/`P1` severity and `READY_TO_FEEDBACK` disposition is the highest
  review priority.
- An `ACTIONABLE_REQUIREMENT` Issue carries `NA` severity even if the reporter labeled it P0;
  publish the requirement classification, not the claimed severity.
- An `ALREADY_FIXED` or `INVALID_AS_REPORTED` Issue carries `NA` severity; propose closing instead
  of commenting as if it were a live defect.
- A `NEEDS_CLARIFICATION` Issue has indeterminate truth; publish a focused question, not a
  severity verdict.
