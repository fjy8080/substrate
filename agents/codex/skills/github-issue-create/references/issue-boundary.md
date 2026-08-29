# Issue drafting severity and task-boundary protocol

## Separate truth, severity, and ownership

- Truth classification says whether current evidence supports the user's text.
- Severity describes demonstrated impact only: `P0` catastrophic security/compliance, irreversible
  data loss, or broad outage; `P1` severe core correctness/security/contract regression; `P2`
  bounded real defect; `P3` minor robustness/maintenance/test/docs defect; `P4` style or optional
  optimization. Use `NA` for pure requirements or unsupported claims. A confirmed duplicate/active
  implementation keeps P0-P4 severity; `ALREADY_FIXED` uses current severity `NA` and may retain a
  separate historical-impact field.
- Ownership identifies the one independently deliverable Issue/WBS area responsible for the work.
- Contract impact is `NONE`, `IMPLEMENT_EXISTING`, or `CHANGE_REQUIRES_DECISION`.
- Publication disposition is `DRAFT_NEW`, `DO_NOT_CREATE_DUPLICATE`, `ACTIVE_WORK_EXISTS`,
  `REFRAME_REQUIRED`, or `NO_PUBLICATION`.

Severity never proves truth, assigns ownership, or authorizes a contract change.

## Bound the draft

Record exact in-scope behavior, explicit exclusions, acceptance, relevant paths/symbols, dependencies,
adjacent task owners, active PRs, and authoritative contract references. A contract constrains the
owned behavior; citing it does not make unrelated endpoints, states, schemas, or future capabilities
part of the Issue.

Fingerprint each authoritative contract as `repository-relative path + Git blob SHA (or stable
section hash) + contract symbol/section + ADR/decision ID when present`, and compare all components
before publication. Approval to publish a decision Issue is never the contract/WBS decision itself.

When one user text spans multiple independent owners, prepare separate proposed drafts or a split
decision for user approval. Do not publish multiple Issues or combine them into one broad Issue
without explicit approval. When ownership or a required contract decision is ambiguous, use
`NEEDS_CLARIFICATION` rather than designing the boundary yourself.

Immediately before publication, revalidate this boundary along with duplicate and active-work state.
A change in owner, scope, dependency, contract impact, or severity evidence is material and requires
a fresh approval of the complete draft.
