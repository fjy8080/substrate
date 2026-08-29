---
name: github-pr-fix
description: Verify and fix active actionable feedback on an existing GitHub pull request using a complete identity/lifecycle ledger, a locked PR task boundary, and P0/P1-only convergence after three review/fix rounds, then report before publishing replies. Use only when the user explicitly invokes `$github-pr-fix` or sends a fix command such as `修复#68` / `修复 #68`. Keep this separate from PR review and Agent Managed Delivery workflows.
---

# GitHub PR Fix

## Keep authority narrow

Treat `修复#<number>` as authorization to inspect the named PR, modify its existing head branch, run
appropriate tests, create focused commits, and push normally to that branch. Do not force-push,
merge, approve, publish replies, resolve threads, re-request review, rerun remote CI, update task
systems, or invoke `$agent-managed-delivery` without separate authority.

The repair authority includes one narrow external mutation required by the authorized push: update
and verify repository-required mechanical PR body metadata for that same PR and exact new HEAD. It
does not authorize changing narrative scope, title, labels, assignees, checklist claims, review
content, or unrelated body text.

Read the repository's `AGENTS.md`, current Git/review rules, relevant contracts, memory, and real
configuration. Preserve unrelated user changes. Use a dedicated worktree when the current worktree
is dirty, belongs to another task, or cannot safely host the PR branch.

Read [repair-scope-and-severity.md](references/repair-scope-and-severity.md). Before coding, freeze a
repair scope manifest from the PR's stated Issue/WBS/output, acceptance, exclusions, authoritative
contract versions, captured head, allowed capabilities/paths, dependencies, and active adjacent
work. Feedback is evidence to verify, not permission to widen this manifest.

## Capture the exact identity and feedback baseline

Resolve the exact `OWNER/REPO` and PR number, then run:

```bash
python3 <THIS-SKILL>/scripts/pr_evidence.py --repo OWNER/REPO --pr NUMBER
```

Read [feedback-lifecycle.md](references/feedback-lifecycle.md) before building the repair ledger.
The snapshot is the source for authenticated actor, PR creator, contribution relation, exact head,
formal reviews, conversation comments, inline threads, review requests, resolution/dismissal events,
and source identities.

Require every relevant `completeness` flag to be true. Snapshot schema 2 takes two complete lifecycle
captures and re-reads the PR, binding title/body, exact head/base, commit/file counts, reviews,
conversation comments, inline comments/threads, timeline, and commit authors to one stable interval.
A timeout, launch failure, malformed page, incomplete commit/author/thread pagination, count mismatch,
or concurrent change is an evidence gap: rerun or stop instead of constructing a mixed-head ledger.

Record these as separate facts:

- who created the PR;
- who is authenticated for the repair;
- whether the authenticated actor contributed commits;
- who authored each feedback item;
- whether the source is a formal Change Request, formal comment/approval, ordinary conversation
  comment, inline thread, or CI failure;
- which commit/head and lifecycle state the source belongs to.

Never describe the authenticated actor's own ordinary comment as colleague feedback. Never call an
ordinary comment a formal Change Request merely because its prose requests changes. An
other-authored PR remains other-authored even when the fixer contributed commits.

Confirm that the PR is open and that its head branch is writable under the user's explicit repair
authority. Write permission alone is not branch ownership. Never assume authority to modify another
contributor's fork; if normal push is unavailable, prepare a local fix and report the blocker.

Inspect the PR template, workflow triggers, metadata validator, and current body before coding.
Record whether the repository requires dynamic PR body fields after every push. For the common
hidden `base/commits/files` contract, use the bundled synchronizer; do not inject that schema into a
repository that does not require it.

## Build a multi-axis repair ledger

Gather every page/cursor of formal reviews, conversation comments, inline threads/replies, dismissal
and review-request timeline events, and current CI/check failures and relevant logs.

Create one ledger entry per distinct claimed defect. Preserve every source URL/ID and author, but
deduplicate multiple sources describing the same defect. Record:

- source type, author, URL/ID, review state, thread state, and source commit;
- lifecycle state from [feedback-lifecycle.md](references/feedback-lifecycle.md);
- claim, file/line, and requested correction;
- reproduction method and pre-fix evidence;
- truth disposition, `P0`-`P4` severity for live defects (`NA` when no live defect remains), scope
  classification, and final result;
- cumulative review/fix round and whether the finding is eligible for this round's code queue.

Truth dispositions are:

- `CONFIRMED`;
- `ALREADY_FIXED`;
- `NOT_REPRODUCIBLE`;
- `INVALID`;
- `NEEDS_CLARIFICATION`.

In rounds 1-3, reproduce each candidate independently on the captured current head. From round 4
onward, fully reproduce potential P0/P1 candidates; perform only bounded verification of clearly
P2-P4 feedback so it can be classified and deferred without expanding the repair. Feedback tied to
an older head must be rechecked rather than silently discarded or assumed active. Only an item that is
`ACTIVE_FEEDBACK + CONFIRMED + IN_PR_SCOPE` and passes the round severity gate enters the code-fix
queue. In rounds 1-3, P0-P4 qualify; from round 4 onward, only P0/P1 qualify. Keep P2-P4 late-round
items and dismissed, resolved, outdated, superseded, informational, or wrong-head sources in the
report without treating them as current repair instructions.

Do not implement a proposed patch blindly. Confirm the underlying defect and its current PR scope.
Ask the user before material scope expansion, architecture/WBS redesign, a contract change not
already owned by the approved PR, or repair that belongs to another PR/task. A contract mismatch
caused by this PR may be repaired within its manifest; revising the contract or importing an
unmerged/future capability requires a user decision.

## Implement confirmed fixes

For each active, confirmed, in-scope, round-eligible item:

1. Add or strengthen a regression test that fails for the reproduced issue when practical.
2. Make the smallest complete correction consistent with authoritative contracts and the PR's
   stated task boundary.
3. Re-run that item's reproduction and record the post-fix result before moving on.
4. Update affected authoritative documentation, tests, migrations, or deployment artifacts only
   when the confirmed fix requires them.

Before every commit, compare both changed paths and changed capabilities with the frozen manifest.
If a finding or discovered defect falls outside it, do not fold it into this PR; report its owner or
request a scope decision. From round 4 onward, do not modify code for P2-P4 even when reproduction
confirms the observation.

After all items, inspect the complete delta from the captured baseline and run repository-required
checks proportional to affected paths. Distinguish local validation from remote CI.

Before pushing, fetch the remote head and rerun the snapshot. If it advanced, inspect the new commits
and rebuild affected ledger entries. Never overwrite remote work or force-push. Create focused
commits, push normally to the existing PR head branch, and verify the new remote SHA.

Before waiting for or interpreting the new CI run, synchronize required PR body metadata immediately:

```bash
python3 <THIS-SKILL>/scripts/sync_pr_metadata.py \
  --repo OWNER/REPO --pr NUMBER --expected-head NEW_FULL_SHA \
  --required-base TARGET_BASE --apply
```

The helper waits for GitHub to expose stable live `head/base/commits/changed_files`, changes only the
recognized visible/hidden dynamic fields, rejects a repository mismatch or wrong base, then re-reads
the body and verifies the narrative was preserved. Require `UPDATED` or `IN_SYNC`. A script error,
concurrent head change, ambiguous duplicate field, incomplete read-back, or another metadata schema
blocks CI handoff; inspect and resolve it instead of claiming the push is complete.

For another repository-specific schema, apply its validator-defined equivalent with the same
exact-HEAD and non-metadata-preservation guarantees. If no dynamic metadata contract exists, record
`NOT_REQUIRED` with the inspected template/workflow evidence. Only after this gate may the repair
observe new CI truthfully. If the metadata job already failed before synchronization completed,
report that result; rerunning remote CI still requires its existing separate authority.

## Report before replying

Report:

- PR number, PR creator, authenticated fixer, PR/contribution relation, branch, original and new
  full head SHAs, and commits;
- the repair ledger with source author/type, lifecycle, reproduction evidence, truth disposition,
  severity, scope classification, round eligibility, and final result for every item;
- the frozen repair manifest and final path/capability drift check;
- changed files and why each changed;
- tests/checks actually run and current remote CI;
- PR metadata contract, synchronization status, live base/commit/file counts, exact head, and body
  read-back evidence;
- compatibility, residual risk, blockers, and rollback point;
- the exact proposed reply for each active source in its original context;
- inactive or duplicate sources that deliberately receive no reply;
- a clear statement that no reply or thread resolution has been published.

Wait for explicit user approval. Requests to change code, rerun tests, or rewrite a response are not
approval to publish.

## Reply after approval

Immediately before replying, rerun the snapshot and compare head SHA, source authors/IDs, formal
review states, thread resolution/outdated status, new replies, and checks. Do not publish stale
replies.

Recheck repository-required PR metadata before replying. If base movement or another push changed
the live statistics, synchronize and verify it again before treating current CI as usable evidence.

Reply in the original context:

- inline feedback receives an inline-thread reply when supported;
- ordinary conversation comments receive a conversation reply/comment and remain identified as
  ordinary comments;
- a formal review body receives an appropriate PR-level response referencing its review ID/URL;
- CI failures are reported in the repair summary, not misrepresented as human feedback.

For confirmed fixes, cite the fixing commit and concise verification evidence. For
`ALREADY_FIXED`, `NOT_REPRODUCIBLE`, or `INVALID`, explain the evidence without claiming a change.
Ask a focused question for `NEEDS_CLARIFICATION`.

For a confirmed P2-P4 item deferred after round 3, use the fixed wording: “已确认，但按第 4 轮起
P0/P1 收敛规则作为非阻塞项延期；本次未修改代码。” Never describe it as fixed or resolved.

Do not resolve a thread, dismiss a review, re-request review, approve, merge, or make further code
changes without separate explicit instruction. Verify every published reply and report its URL or
identifier.
