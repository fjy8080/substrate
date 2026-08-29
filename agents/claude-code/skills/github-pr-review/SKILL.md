---
name: github-pr-review
description: Perform a read-only, exact-HEAD GitHub pull-request review with PR-creator identity, contributor independence, task-boundary classification, and P0/P1-only convergence after three review/fix rounds, then publish only after user confirmation. Use only when the user explicitly invokes `/github-pr-review` or sends an explicit PR-review command such as `审查#123` / `审查 #123`. Keep this separate from development, repair, and delivery workflows.
---

# GitHub PR Review

## Preserve the review boundary

Treat `审查#<number>` as authorization to inspect and report, not authorization to publish. Make no
repository, branch, PR, issue, CI, or task-system changes during inspection. Do not implement fixes,
invoke `/github-pr-fix`, or invoke `/agent-managed-delivery`.

Read the repository's `AGENTS.md`, current review/Git rules, relevant authoritative contracts, and
real configuration. Re-check live GitHub state; do not rely on memory.

Read [severity-and-scope.md](references/severity-and-scope.md). Before searching for blockers,
freeze a read-only review boundary manifest from the PR's stated task/WBS/Issue, acceptance criteria,
explicit exclusions, authoritative contract versions, base/head, changed capabilities/paths,
dependencies, and adjacent active work. A broad contract describes how the PR must behave; it does
not make every capability in that contract part of this PR.

## Capture identity and feedback first

Resolve the exact `OWNER/REPO` and PR number, then run:

```bash
python3 ~/.claude/skills/github-pr-review/scripts/pr_evidence.py --repo OWNER/REPO --pr NUMBER
```

Read [identity-and-publication.md](references/identity-and-publication.md) before classifying or
publishing. Use the snapshot as the identity/event ledger; inspect the full PR diff and checks with
additional read-only commands.

Require every relevant `completeness` flag to be true. Snapshot schema 2 takes two complete lifecycle
captures and re-reads the PR, binding title/body, exact head/base, commit/file counts, reviews,
conversation comments, inline comments/threads, timeline, and commit authors to one stable interval.
A timeout, launch failure, malformed page, incomplete commit/author/thread pagination, count mismatch,
or concurrent change is an evidence gap: rerun or stop instead of inferring identity, round, or scope.

Never collapse these dimensions:

- `pr_relation`: whether the authenticated actor is the actual PR creator;
- `contribution.status`: whether that actor appears as a commit/co-author contributor;
- `independence`: whether repository rules allow the review to count as independent;
- `publication_route`: ordinary comment versus formal GitHub review.

Only `SELF_PR` is an authorized self-review. `OTHER_PR` never becomes self-review because the actor
co-authored commits, owns the repository, can write the branch, or later supplied fixes. Those facts
may produce `NON_INDEPENDENT_CONTRIBUTOR`, but the PR remains other-authored.

If `pr_relation` is unknown or required evidence is incomplete, stop before publication and ask the
user. Unknown contribution prevents claiming independent approval; it does not change an
other-authored PR into a self PR.

## Inspect the exact PR

1. Read the PR body, linked task, base/head repositories and branches, full head SHA, commits,
   changed files, complete diff, formal reviews, conversation comments, inline threads, timeline,
   review requests, and current checks. Exhaust every page/cursor.
2. Derive the actual merge base and inspect relevant unchanged context. Map the diff to the frozen
   review boundary and identify adjacent WBS/Issue/PR ownership before assigning any blocker. Review correctness,
   regressions, security/privacy, contracts, concurrency/failure behavior, tests, documentation,
   migration/deployment, and repository gates in proportion to the change.
3. Bind every conclusion to the captured full head SHA. If the head changes, invalidate the result
   and review the complete new HEAD.
4. Run only relevant read-only diagnostics. Do not dispatch or rerun remote CI without separate
   authority. Distinguish observed CI from locally run checks.
5. Check existing feedback so the proposed review does not duplicate an active finding or ignore a
   dismissal, resolution, newer review, or later fix.
6. Derive the cumulative review round from explicit metadata and the complete feedback/head
   lifecycle. Never reset it because the head, reviewer, publication route, or wording changed.
   In rounds 1-3, all confirmed in-PR defects may block. From round 4 onward, focus blocker search on
   P0/P1; observed P2-P4 findings remain non-blocking and cannot justify `REQUEST_CHANGES`.

## Report for user verification

Lead with blocking findings ordered by severity. For each live observation, give its `P0`-`P4`
severity; use `NA` only for `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `INVALID`. Also give its
scope classification, file/line, deterministic trigger, impact, evidence, and the smallest acceptable
correction. Separate non-blocking suggestions and late-round P2-P4 observations. Do not promote a
predecessor defect, unmerged dependency, future task, WBS ambiguity, or hardening suggestion into a
current-PR blocker. A scope/contract decision that makes review impossible is a user blocker, not a
request for this PR author to redesign the task.

Include:

- PR number, creator, base, and reviewed full head SHA;
- authenticated actor;
- PR relation, contribution relation, independence status, review-request context, and publication
  route as separate fields;
- findings, open questions, and existing-feedback reconciliation;
- frozen review boundary, cumulative round, active severity threshold, and deferred finding count;
- checks actually observed or run;
- exact proposed GitHub action and body;
- a machine-readable footer containing `review_round`, `reviewed_head_sha`, `severity_gate`,
  eligible blocker count, deferred P2-P4 count, and scope-classification counts;
- a clear statement that nothing has been published.

Wait for explicit user confirmation. Editing, re-checking, or discussing findings is not publication
approval.

## Publish after confirmation

Immediately before publishing, rerun the snapshot and re-read the exact head, PR creator, new
commits, reviews, comments, and threads. Do not publish stale or materially reclassified evidence.

### `SELF_PR`

Never formally approve or request changes on a PR created by the authenticated actor. Publish an
ordinary PR conversation comment whose first line is:

`授权自审查（不计入独立 Review / Approve）`

Include the reviewed head SHA and findings. State that it is an authorized self-review record, does
not satisfy independent Review, and does not authorize merge.

### `OTHER_PR` with blocking findings

Submit a formal GitHub `REQUEST_CHANGES` review. This route is determined by the actual PR creator,
not by commit contribution.

- If project rules confirm independence, label it independent review.
- If the actor contributed, label it `贡献者审查（不计入独立 Review / Approve）`; do not call it
  authorized self-review.
- If independence is unknown, disclose that it is unverified and never claim an independent
  approval gate.

Include the exact reviewed head SHA and actionable findings. Verify that GitHub recorded the formal
review and report its URL or identifier.

`REQUEST_CHANGES` is allowed only when at least one finding is both `IN_PR_DEFECT` and eligible under
the round's severity threshold. From round 4 onward that means P0/P1 only. P2-P4 items may remain in
the review body as explicitly non-blocking observations.

### `OTHER_PR` without blocking findings

Do not invent a blocker. Report the no-blocking result, including every non-blocking observation,
and ask for explicit direction:

- formal `APPROVE` is permitted only when project rules confirm independence;
- a contributor or unknown-independence actor must not approve and may propose formal `COMMENT` or
  no publication.

## Keep authority narrow

Publishing does not authorize code changes, thread resolution, CI reruns, review re-request,
approval beyond the confirmed action, merge, task updates, or memory updates.
