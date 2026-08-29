# Issue review publication protocol

## No formal review mechanism on Issue threads

GitHub Issues have no `APPROVE` / `REQUEST_CHANGES` equivalent. Every publication under this skill
is an **ordinary Issue comment** (or a close-with-comment, or a label change). Never frame an Issue
comment as a release-gate approval, a formal review, or an independent approval. Release gates,
independence, and merge approval belong to `/github-pr-review`, not here.

## Disclose the reviewer's role in every published comment

Unlike PR review, the reviewer-vs-PR-creator axis does not apply. Instead, disclose the reviewer's
relationship to **the Issue and its owned task**:

| Reviewer role | Header line | Meaning |
|---|---|---|
| Reviewer ≠ reporter, ≠ task owner | `审查反馈（第三方审查）` | Ordinary triage feedback |
| Reviewer = reporter of this Issue | `自查反馈（审查者 = 报告人，仅记录）` | Self-assessment; not authoritative |
| Reviewer = owner of the WBS task this Issue concerns | `自查反馈（审查者 = 任务负责人，非独立）` | Self-assessment; disclose conflict of interest |
| Reviewer contributed to the code under report | `贡献者审查（不计入独立审查）` | Disclose contribution; not independent |
| Independence unknown / unverified | `审查反馈（独立性未核实）` | Never claim an independent approval gate |

Pick the most accurate single header. When the reviewer wears multiple hats, disclose all relevant
roles; never collapse them to a stronger-sounding label. The header is mandatory in every published
comment.

## Exact-evidence publication check

Before publishing any comment/close/label, rerun the evidence script and re-read each target Issue:

- Issue state, body, comments, labels, assignee (did the reporter withdraw or clarify?);
- newly linked PRs or commits since the triage snapshot (is it now `ALREADY_FIXED`?);
- the `origin/develop` SHA at triage time vs now (did the root cause change?);
- other Issues in the same duplicate/related cluster (did the canonical Issue move?).

If a material delta invalidates truth, severity, ownership, or the relationship graph, do not
publish. Re-triage and present the new classification. A small wording delta may only require
refreshing the comment body; a truth or ownership delta requires fresh user approval.

## What each publication action requires

- **Comment**: explicit user approval of the comment body for that Issue. The body must include the
  five-dimension classification, the inspected `origin/develop` SHA, the contract fingerprint (if
  any), the recommended action, and the role-disclosure header.
- **Close**: explicit user approval, and only when truth is `ALREADY_FIXED` (cite the fixing
  commit/PR) or `INVALID_AS_REPORTED` (cite the contradicting authoritative contract). Closing a
  `P0-blocker` Issue additionally requires the project-required decision-maker's approval.
- **Label**: explicit user approval of the exact label set. Never invent new labels silently; if a
  new label is needed, propose it first and let the user (or the project's label maintainer) create
  it on GitHub.
- **Assignment / milestone edits**: not performed under this skill. If the triage suggests an
  assignee or milestone, recommend it in the comment; do not apply it.

## Batch publication

When the user approves publication on multiple Issues:

- Publish serially, one Issue at a time, re-reading the Issue immediately before each comment.
- A `DUPLICATE` cluster can share a canonical paragraph, but each Issue still receives its own
  comment with its own header and a pointer to the canonical Issue.
- Stop and re-confirm if a later Issue's state changed during the batch (e.g. the reporter replied
  after seeing an earlier comment on a related Issue).
- Report after each publication: Issue number, action taken, comment URL, and the exact SHA at
  publication.

## What publication never authorizes

- No code change, branch, commit, push, or PR (use `/github-issue-debug` for repair).
- No closure of a `P0-blocker` without the project-required decision.
- No contract/WBS change under the guise of "triage feedback" — `CHANGE_REQUIRES_DECISION` stays
  non-actionable until the CHG/ADR decision is recorded.
- No follow-up comment on an adjacent Issue the user did not approve.
- No assignment, milestone, or label change beyond the explicitly approved set.
- No memory or authoritative-docs mutation as a side effect of publication. If triage surfaces a durable
  project fact, recommend a separate documentation task; do not edit authoritative sources silently.
- No override of another Issue's owner or another actor's open PR.

## Switching workflows

If during triage the user decides to actually repair a confirmed Issue, stop this skill's
publication phase and switch to `/github-issue-debug`. That skill enforces its own plan-approval
gate, isolated-branch/worktree creation, and PR handoff; it never reuses this skill's comment as
plan approval. If the user wants to review a PR that claims to fix a triaged Issue, use
`/github-pr-review` under its own trigger and identity rules — this skill's triage classification is
evidence for that review, not a substitute for it.
