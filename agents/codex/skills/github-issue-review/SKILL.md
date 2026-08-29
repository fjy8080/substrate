---
name: github-issue-review
description: Read-only triage/audit of one or more GitHub Issues against current code, live work, and authoritative contracts. Classify truth, severity, task/WBS ownership, contract impact, duplicates, and reproducibility, then publish issue comments only after explicit user confirmation. Use only when the user explicitly invokes `$github-issue-review` or sends `审查issue` / `审查 issue` with one or more Issue numbers. Never infer this workflow from ordinary discussion, PR review, implementation, or delivery requests. This skill never creates branches, commits, PRs, or code changes; for repair use `$github-issue-debug` instead.
---

# GitHub Issue Review (Triage/Audit)

## Preserve the review boundary

Treat `审查issue #<number>...` as authorization to **inspect and report**, never to publish, edit
code, create branches/worktrees, commit, push, file PRs, close Issues, or change labels without
separate user confirmation. Keep this workflow strictly separate from `$github-issue-debug`,
`$github-pr-fix`, and `$agent-managed-delivery`.

Read the repository's `AGENTS.md`, current Git/PR rules, Issue templates, authoritative contracts
(API/field/state semantics, business rules, ADR, milestones), current configuration, and memory.
Re-check live GitHub state; never rely on memory for Issue body, comments, labels, state, or
open-PR inventory. Repository rules may add stricter gates; never weaken them.

Read [triage-dimensions.md](references/triage-dimensions.md) and
[publication-protocol.md](references/publication-protocol.md) before classifying or publishing.

## Capture complete current evidence

This skill reuses `github-issue-debug`'s evidence script unchanged. Run it from the repository in
scope, passing every requested Issue explicitly:

```bash
python3 ~/.codex/skills/github-issue-debug/scripts/issue_evidence.py \
  --issue 12 --issue 34 --target-base develop
```

Require every relevant snapshot `completeness` flag to be true. A failed remote-head query,
unreadable worktree status, incomplete open-PR files/reviews/comments/commits, count mismatch,
concurrent movement, or >40 open PRs means the parallel-work audit is incomplete: resolve the gap
or stop and report it instead of presenting a triage result. Never downgrade a missing-evidence
state to "no conflict" or "no duplicate."

If the current repository does not match the user's scope, an Issue number resolves to a PR (not an
Issue), or the remote `develop` branch does not exist, stop.

## Inspect each Issue against current truth

For every requested Issue:

1. Read its full body, comments, timeline, labels, owner/assignee/state, linked work (PRs, commits,
   other Issues), and any acceptance evidence already on the thread.
2. Inspect relevant code, tests, configuration, contracts, blame/history, and attempt a faithful
   read-only reproduction against current `origin/develop`. Do not mutate code or data.
3. Check all open PRs (exact heads/bases, related Issue references), active branches/worktrees and
   their dirty state, and other work touching the same files or behavior. An open PR with no Issue
   link may still conflict or already fix this Issue by file or behavior — search linkage and diff.
4. Cross-check the Issue's claim against authoritative contracts: API contract (`docs/03-接口契约/`),
   business rules (`docs/知识库/business-rules.md`, `docs/05-业务规则/`), ADR (`docs/adr/`),
   milestones/Flyway (`docs/知识库/milestones.md`), and permission model. A claim that contradicts
   an authoritative source is not a defect; record the contract fingerprint.
5. Across all requested Issues, detect duplicates, overlaps, and dependencies. Two Issues are
   `DUPLICATE` only when their confirmed root cause and owned scope are the same; partial overlap is
   `RELATED` not `DUPLICATE`. Record the relationship graph before reporting.

## Classify on five independent dimensions

Per [triage-dimensions.md](references/triage-dimensions.md), record each dimension separately.
None substitutes for another — a P0 claim is not automatically true, a confirmed Issue may still be
out of current scope, and a contract reference does not import the whole contract.

1. **truth**: `CONFIRMED`, `PARTIALLY_CONFIRMED`, `ACTIONABLE_REQUIREMENT`, `ALREADY_FIXED`,
   `NOT_REPRODUCIBLE`, `INVALID`, `NEEDS_CLARIFICATION`.
2. **severity**: `P0`/`P1`/`P2`/`P3`/`P4` for a proven current defect; `NA` for a pure requirement
   or unsupported claim.
3. **task ownership**: `CURRENT_ISSUE`, `PREDECESSOR_TASK`, `UNMERGED_DEPENDENCY`, `FUTURE_TASK`,
   `AMBIGUOUS_OWNER`.
4. **contract impact**: `NONE`, `IMPLEMENT_EXISTING`, `CHANGE_REQUIRES_DECISION`.
5. **review disposition** (this skill's action axis):
   - `READY_TO_FEEDBACK` — truth confirmed, ready to publish triage feedback to the reporter;
   - `EXTERNAL_BLOCKED` — needs environment/credential/owner decision unavailable now;
   - `DUPLICATE` — same root cause/scope as another Issue (cite which);
   - `RELATED` — overlaps with another Issue but not identical;
   - `ALREADY_FIXED` — current `develop`/PR already fixes it; propose closing with evidence;
   - `INVALID_AS_REPORTED` — contradicts authoritative behavior or false premise; propose closing;
   - `NEEDS_REPRO` — missing reproduction steps/data/version; ask the reporter;
   - `NEEDS_DECISION` — requires CHG/ADR decision before any action (do not speculate).

## Present a per-Issue triage table and cross-Issue map

For each Issue, present:

- Issue number, URL/title, reporter, current labels/state;
- the five-dimension classification in a single row;
- reproduced root cause or remaining uncertainty (with file:line and the exact `origin/develop` SHA
  inspected);
- contract fingerprint that confirms or refutes the claim;
- relationship to other requested Issues (duplicate/related/dependency);
- recommended feedback to the reporter (one short paragraph) and the recommended GitHub action
  (`comment`, `close`, `label`, or `external` — no action taken yet);
- open questions that need the reporter or maintainer.

When more than one Issue is requested, also produce a **cross-Issue map**:
- duplicate/related clusters (which Issues can be merged or should cross-reference);
- dependency order (which Issue blocks another);
- severity-ranked backlog (P0 first), with `READY_TO_FEEDBACK` vs blocked count;
- recommended batch vs serial feedback order.

State clearly that **nothing has been published, closed, labeled, or assigned.** Wait for explicit
user confirmation. Editing the report, answering questions, or approving one Issue authorizes only
that Issue's publication, not the rest.

## Publish after confirmation

Immediately before publishing, rerun the evidence script and re-read each Issue's body, comments,
labels, state, and any newly linked PRs. Do not publish stale or materially reclassified evidence.
Compare the to-be-published findings to the current Issue state:

- if the Issue was closed, relabeled, or received new evidence since the triage snapshot, pause and
  re-triage;
- if a new PR now fixes it, reclassify to `ALREADY_FIXED` and ask before commenting;
- if the reporter withdrew or clarified the claim, re-truth before publishing.

Read [publication-protocol.md](references/publication-protocol.md). Issue threads have no formal
review mechanism — every publication is an **ordinary Issue comment**, not `APPROVE` or
`REQUEST_CHANGES`. The reviewer-vs-reporter-vs-task-owner relationship is disclosed in the comment
header; it is never framed as an independent approval gate.

Per Issue, publish only what the user approved:

- **Comment**: the triage result, root cause or uncertainty, contract reference, duplicate/related
  pointers, and the smallest actionable ask from the reporter. Lead with a header line that discloses
  the reviewer's role (e.g. `审查反馈（审查者 ≠ 报告人）` or `自查反馈（审查者 = 任务负责人，仅记录非独立）`).
- **Close** (only when truth is `ALREADY_FIXED` or `INVALID_AS_REPORTED` and the user explicitly
  approved): include the fixing commit/PR or the authoritative contract that contradicts the claim.
- **Label** (only with explicit approval): propose or apply the agreed label set; never invent new
  labels silently.

Never use this skill to approve a release gate, close a `P0-blocker` without the project-required
decision, or override another Issue's owner. Findings that would require `CHANGE_REQUIRES_DECISION`
stay non-actionable until the formal CHG/ADR decision is recorded by the role the project requires.

## Keep authority narrow

Publication authorizes only the confirmed comment/close/label on the specified Issues. It does not
authorize follow-up code, thread resolution on adjacent Issues, CI reruns, assignment changes,
milestone edits, or memory updates. If the reporter's reply changes truth, re-run triage under this
skill before publishing again.

When the user wants to actually **repair** a confirmed Issue, switch to `$github-issue-debug`, which
enforces its own plan-approval + isolated-branch + PR-handoff gates. This skill never produces a
repair branch or PR.
