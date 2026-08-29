---
name: github-issue-create
description: Turn user-provided text into a code-verified, severity-classified, task-bounded GitHub Issue draft for the current repository, then publish only after explicit user approval. Use only when the user explicitly invokes `$github-issue-create` or sends a request containing `创建issue` / `创建 issue` followed by the source text. Do not use for ordinary discussion, PR review, implementation, or automatic issue publication.
---

# GitHub Issue Create

## Keep publication gated

Treat `创建issue` plus text as authorization to inspect the current repository and prepare a draft,
not authorization to publish. Do not edit code, create branches, change labels, or write to GitHub
before the user approves the exact draft.

Read the current repository's `AGENTS.md`, issue/Git rules, Issue templates, relevant authoritative
documents, real configuration, and code. Preserve unrelated local changes.

## Resolve and snapshot the current repository

Run from the repository in scope:

```bash
python3 <THIS-SKILL>/scripts/issue_evidence.py
```

Use the returned `name_with_owner` as the only publication target. Do not infer the repository from
an Issue number, chat history, directory name, or another open project. If repository identity is
ambiguous or mismatched, stop and ask the user.

Inspect the snapshot's `completeness` flags. Do not claim that duplicate or active work checks are
complete while any relevant flag is false, including fully paginated open-PR files, commits, reviews,
conversation comments, and inline comments; resolve the gap or disclose it and stop before requesting
publication approval.

Snapshot schema 2 also verifies a repository-matching remote, stable target branch, requested Issues,
open-Issue/open-PR inventories, labels, local worktrees, remote heads, and each PR's identity,
title/body/head/base/counts. Command timeout or launch failure, malformed data, count mismatch,
concurrent movement, more than 40 open PRs, or a PR beyond the REST endpoints' provable file/commit
limits is a fail-closed evidence gap, never proof that no duplicate or active work exists.

Read [issue-draft-protocol.md](references/issue-draft-protocol.md) and
[issue-boundary.md](references/issue-boundary.md) before drafting or publishing.

## Verify the user's text

1. Preserve the user's intent while separating observed facts, assumptions, requested behavior, and
   proposed solutions.
2. Locate the relevant code, tests, configuration, contracts, and recent history. Reproduce the
   claim when safe and proportionate. Do not modify files.
3. Search open and closed Issues and open/merged PRs using distinctive terms, affected symbols, and
   error messages. The snapshot's open lists are a starting point, not a substitute for semantic
   duplicate search.
4. Record truth as `CONFIRMED`, `PARTIALLY_CONFIRMED`, `VALID_REQUIREMENT`,
   `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, or `NEEDS_CLARIFICATION`. Separately record publication
   disposition as `DRAFT_NEW`, `DO_NOT_CREATE_DUPLICATE`, `ACTIVE_WORK_EXISTS`,
   `REFRAME_REQUIRED`, or `NO_PUBLICATION`; duplicate/active work never erases proven severity.
5. Remove secrets, tokens, private endpoints, full personal data, and unsafe logs from the draft.
6. For a proven live defect, assign `P0`-`P4`; pure requirements and unsupported claims use `NA`.
   `ALREADY_FIXED` uses current severity `NA` and may separately retain historical impact. A
   confirmed duplicate or active implementation keeps its P0-P4 severity while publication is blocked.
   Separately identify the owning Issue/WBS area, adjacent exclusions, dependencies, and whether the
   proposal implements an existing contract or asks for a contract decision.

Do not manufacture code evidence for a product request. Do not publish a known duplicate or an
incorrect defect claim merely because the user used the trigger; explain the evidence and propose
the existing Issue/PR or a corrected framing.

Do not combine unrelated owners merely because they appeared in one user paragraph. If the text
contains multiple independently deliverable tasks or conflicting contract owners, propose bounded
drafts/splits and obtain explicit approval; never hide the expansion in one Issue.

## Present the exact draft

Report:

- current `OWNER/REPO`, inspected HEAD, and evidence timestamp;
- verification classification and code/reproduction evidence;
- severity, task/WBS owner, explicit in/out scope, dependency owner, and contract impact;
- publication disposition and any existing Issue/PR owner;
- duplicate and active-PR search results;
- exact proposed title, body, and existing labels;
- assumptions or questions;
- a clear statement that nothing has been published.

Use the repository's Issue template where applicable. Keep acceptance criteria testable and avoid
over-prescribing an implementation unless the code evidence makes it necessary.

Wait for explicit approval to publish the shown draft. Corrections, questions, or requests to edit
the text are not publication approval. Re-present the complete changed draft after every edit.

## Refresh and publish after approval

Immediately before publication, rerun `issue_evidence.py` and repeat targeted duplicate/PR searches.
If the repository, relevant HEAD/code, duplicate status, labels, active implementation work, task
owner, scope/dependency, or contract impact changed materially, do not consume the stale approval.
Show the delta and request approval again.

Publish exactly the approved title, body, and existing labels to the snapshot repository. Do not
create labels, assign users, add a milestone/project, or split one draft into multiple Issues without
separate approval.

Approval to publish a decision-seeking Issue is not approval of the contract/WBS decision described
inside it. This Skill never converts `CHANGE_REQUIRES_DECISION` into implementation authority.

After creation, re-read the Issue and verify repository, number, title, body, labels, author, and URL.
Report the URL and any server-side normalization. Editing, closing, assigning, or commenting on the
new Issue requires separate authority.
