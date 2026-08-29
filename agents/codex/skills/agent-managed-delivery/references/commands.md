# Controller commands

Set the script path from the installed skill:

```bash
WORKFLOWCTL="$HOME/.codex/skills/agent-managed-delivery/scripts/workflowctl.py"
```

Use `python3 "$WORKFLOWCTL" status` before resuming an existing task.

## Initialize supervised mode

```bash
python3 "$WORKFLOWCTL" init \
  --batch-id BATCH-ID --mode SUPERVISED \
  --remote REMOTE --base BASE-BRANCH
python3 "$WORKFLOWCTL" candidate --task-id TASK-01 --title "Task title"
```

## Initialize delegated batch mode

```bash
python3 "$WORKFLOWCTL" init \
  --batch-id BATCH-ID --mode DELEGATED_BATCH \
  --remote REMOTE --base BASE-BRANCH \
  --task 'TASK-01::First task' \
  --task 'TASK-02::Second task' \
  --delegate-create-pr --delegate-merge \
  --evidence 'User explicitly delegated these already-claimed tasks'
```

Pass every task explicitly; never generate ranges that were not named by the user.

## Claim and lock scope

Record the WBS-owned output before development. `--allowed-path` is a repository-relative glob. Dependencies use `TASK-ID::STATUS`.

```bash
python3 "$WORKFLOWCTL" claim \
  --task-id TASK-01 --evidence 'User claim or batch claim evidence'
python3 "$WORKFLOWCTL" advance --to EXPLORING
python3 "$WORKFLOWCTL" scope-record \
  --wbs-source 'WBS section or row' \
  --independent-output 'The independently deliverable result owned by TASK-01' \
  --acceptance 'Acceptance criteria owned by TASK-01' \
  --test-requirement 'Tests required for TASK-01' \
  --authoritative-input 'Authoritative API/design/security document' \
  --in-scope 'Capability owned by TASK-01' \
  --out-of-scope 'Adjacent capability owned by TASK-02' \
  --dependency 'TASK-00::MERGED' \
  --allowed-path 'backend/app/owned_area/**' \
  --allowed-path 'backend/tests/owned_area/**' \
  --evidence 'WBS, dependency, and authority audit'
python3 "$WORKFLOWCTL" scope-check \
  --status PASS --evidence 'Baseline and planned-path audit'
python3 "$WORKFLOWCTL" advance --to DEVELOPING
```

Broad architecture or API documents define how an owned output must behave; citing them does not import every capability mentioned in them into the task.

## Implement, test, document, and report

After every commit, rebase, conflict resolution, or other HEAD change, synchronize and re-run the exact-HEAD scope check before recording further gates.

```bash
python3 "$WORKFLOWCTL" sync-head
python3 "$WORKFLOWCTL" scope-check \
  --status PASS --evidence 'Changed paths and capability diff remain within scope revision 1'
python3 "$WORKFLOWCTL" advance --to SELF_TESTING
python3 "$WORKFLOWCTL" self-test --status PASS --evidence 'commands and results'
python3 "$WORKFLOWCTL" advance --to IMPLEMENTATION_READY_FOR_DOCS
python3 "$WORKFLOWCTL" advance --to DOCUMENTING
python3 "$WORKFLOWCTL" docs-gate \
  --status PASS --evidence 'updated/scanned docs and validation'
python3 "$WORKFLOWCTL" report --summary 'complete task report'
```

When a changed path is outside the allowlist, or a capability/dependency drift trigger is found, record a blocked scope check and use the dedicated scope-block flow. Never make the scope check pass by broadening the glob after the fact.

## Create or refresh the same PR

In `SUPERVISED`, record the user's exact-HEAD permission before first PR creation:

```bash
python3 "$WORKFLOWCTL" approve --action create_pr --evidence 'user approval'
```

Create the Ready PR and bind its persistent identity from live GitHub evidence:

```bash
python3 "$WORKFLOWCTL" advance --to PR_CREATING
python3 "$HOME/.codex/skills/agent-managed-delivery/scripts/sync_pr_metadata.py" \
  --repo OWNER/REPO --pr 123 --expected-head FULL-HEAD-SHA \
  --required-base BASE-BRANCH --apply
python3 "$WORKFLOWCTL" attach-pr \
  --number 123 --url PR-URL --base BASE-BRANCH \
  --template-complete --mergeable MERGEABLE \
  --metadata-status PASS \
  --metadata-evidence 'sync helper UPDATED/IN_SYNC; live body read-back hash and counts'
python3 "$WORKFLOWCTL" advance --to CI_PENDING
python3 "$WORKFLOWCTL" ci \
  --status PASS --source github-live \
  --evidence 'required checks on exact HEAD'
python3 "$WORKFLOWCTL" advance --to REVIEW_REQUESTED
python3 "$WORKFLOWCTL" advance --to REVIEWING
```

Run the synchronizer only when repository inspection confirms the supported hidden
`base/commits/files` contract. It waits for stable live GitHub statistics, preserves non-metadata
body text, and verifies the body after the update. For another schema, perform its validator-defined
equivalent before `attach-pr`. If template/workflow/validator inspection proves there is no dynamic
body metadata, use `--metadata-status NOT_REQUIRED` and put that audit in `--metadata-evidence`.
Never use `NOT_REQUIRED` merely because synchronization failed.

Later fixes may refresh the same bound PR without another `create_pr` approval. They still create a new HEAD and therefore invalidate scope, self-test, docs, report, CI, review, and merge evidence. The controller refuses to attach a different PR number to the task.
Every such refresh must repeat the metadata synchronization/read-back and `attach-pr` evidence before
returning to `CI_PENDING`.

## Triage review findings before publishing

Each finding is JSON with a stable ID, WBS category, `P0`-`P4` severity, reproduction evidence, and
the WBS/scope basis. In rounds 1-3 all `IN_SCOPE_DEFECT` entries block. From round 4 onward only
P0/P1 entries block; P2-P4 stay in the published deferred section and are not sent to Developer.

```bash
python3 "$WORKFLOWCTL" review-triage \
  --round 1 \
  --finding-json '{"id":"F-001","category":"IN_SCOPE_DEFECT","severity":"P1","summary":"Owned behavior is incorrect","reproduction":"Failing test or deterministic steps","scope_basis":"Named TASK-01 acceptance criterion","source":"reviewer"}' \
  --scope-audit-evidence 'Compared exact PR diff with scope revision 1 and adjacent WBS rows'
python3 "$WORKFLOWCTL" review \
  --verdict CHANGES_REQUIRED_BY_COMMENT --blocking 1 --round 1 \
  --evidence 'published ordinary comment URL'
python3 "$WORKFLOWCTL" advance --to FIXING_REVIEW
```

The published changes-required record freezes a repair whitelist containing only eligible
`IN_SCOPE_DEFECT` IDs. After Developer creates the repair HEAD, record exactly that set before the
scope check:

```bash
python3 "$WORKFLOWCTL" sync-head
python3 "$WORKFLOWCTL" review-fix-record \
  --finding-id F-001 \
  --changed-capability 'Correct the TASK-01 owned terminal transition' \
  --evidence 'Compared complete repair diff with F-001 and scope revision 1; no deferred finding changed'
python3 "$WORKFLOWCTL" scope-check \
  --status PASS --evidence 'Repair HEAD changes only the whitelisted finding and approved capability'
```

The resolved ID set must exactly equal the whitelist. P2-P4 deferred IDs cannot be added, even when
they share a file with P0/P1 work. A later commit invalidates the record and requires a fresh exact-HEAD
`review-fix-record`. This remains true after leaving `FIXING_REVIEW`: until the next published Review,
any new HEAD reopens the audit. Follow the normal late-HEAD transition back to `DEVELOPING` (or use
`FIXING_CI` for an actual CI repair), record the same whitelist against the new HEAD, then run
`scope-check PASS`.

For a clean round:

```bash
python3 "$WORKFLOWCTL" review-triage \
  --round 2 --clean \
  --scope-audit-evidence 'Exact-HEAD scope and authority audit' \
  --prior-round-delta 'F-001 fixed; reviewed the changed path and its callers'
python3 "$WORKFLOWCTL" review \
  --verdict APPROVED_FOR_MERGE_BY_COMMENT --blocking 0 --round 2 \
  --evidence 'published ordinary comment URL'
```

Round 2 and later must provide `--prior-round-delta`; the review must cover both the fix delta and regression risk without silently expanding WBS ownership.

After three rounds, a real P2-P4 finding is recorded but cannot create another repair loop:

```bash
python3 "$WORKFLOWCTL" review-triage \
  --round 4 \
  --finding-json '{"id":"F-009","category":"IN_SCOPE_DEFECT","severity":"P2","summary":"Bounded edge case","reproduction":"Deterministic but non-core edge case","scope_basis":"Current task, does not block core acceptance","source":"reviewer"}' \
  --scope-audit-evidence 'Exact-HEAD P0/P1-focused scope audit' \
  --prior-round-delta 'Round 3 fixes passed; no P0/P1 regression found'
python3 "$WORKFLOWCTL" review \
  --verdict APPROVED_FOR_MERGE_BY_COMMENT --blocking 0 --round 4 \
  --evidence 'published ordinary comment URL with F-009 in deferred observations'
```

The controller derives the blocking threshold from the cumulative round and rejects a reset to an
earlier round after a HEAD, Reviewer, or scope change.

To correct an unpublished triage in the same round, rerun it with `--replacement-reason`. The old
full finding set remains in `review_triage_history`; after publication the same round cannot be
replaced.

Valid categories are:

- `IN_SCOPE_DEFECT`
- `PREDECESSOR_DEFECT`
- `UNMERGED_DEPENDENCY`
- `FUTURE_WBS_GAP`
- `WBS_AMBIGUITY`
- `HARDENING_SUGGESTION`
- `NOT_REPRODUCIBLE`
- `ALREADY_FIXED`
- `INVALID`

`PREDECESSOR_DEFECT`, `UNMERGED_DEPENDENCY`, and `WBS_AMBIGUITY` prevent a normal review verdict. Enter `SCOPE_BLOCKED` and request a user decision instead.

In round 4 and later, P2-P4 instances of those scope categories are non-blocking observations. If
the ambiguity or dependency truly prevents current acceptance, its actual impact is P0/P1 and the
normal `SCOPE_BLOCKED` rule applies.

`NA` is valid only for `NOT_REPRODUCIBLE`, `ALREADY_FIXED`, and `INVALID`; all other categories need
P0-P4. `HARDENING_SUGGESTION` cannot be P0/P1. P0/P1 `FUTURE_WBS_GAP` also enters `SCOPE_BLOCKED`
in every round because the WBS/dependency design conflicts with current safe acceptance.

## Stop for scope or WBS decisions

```bash
python3 "$WORKFLOWCTL" scope-block \
  --condition 'Review exposed an unmerged dependency outside TASK-01 ownership' \
  --evidence 'finding F-002 and dependency/branch evidence' \
  --investigation 'reproduced the failure and checked the dependency PR/base status' \
  --option 'Wait for the dependency PR to merge, then rebase and re-audit' \
  --option 'Owner explicitly revises the WBS/task boundary' \
  --required-action 'User chooses dependency handling or approves a scope revision'
```

Waiting for an existing dependency does not authorize edits to that dependency. If the user explicitly changes the current task boundary, record the complete replacement manifest; the controller increments the scope revision and returns to `EXPLORING`:

```bash
python3 "$WORKFLOWCTL" scope-change \
  --wbs-source 'User-approved revised WBS source' \
  --independent-output 'Revised independently deliverable result' \
  --acceptance 'Revised acceptance criteria' \
  --test-requirement 'Revised tests' \
  --authoritative-input 'Applicable authority source' \
  --in-scope 'Explicitly approved capability' \
  --out-of-scope 'Still excluded adjacent capability' \
  --dependency 'TASK-00::MERGED' \
  --allowed-path 'backend/app/owned_area/**' \
  --evidence 'Re-audited WBS and impact' \
  --approval-evidence 'Exact user decision approving scope revision 2'
python3 "$WORKFLOWCTL" scope-check \
  --status PASS --evidence 'Revision 2 exact-HEAD audit'
python3 "$WORKFLOWCTL" advance --to DEVELOPING
```

For a legacy in-flight runtime created before scope locking existed, first enter `SCOPE_BLOCKED` and obtain a user decision. The same `scope-change` command may adopt revision 1 only when `--baseline-head FULL-40-CHAR-SHA` identifies the original task baseline and Git verifies that it is an ancestor of the current HEAD. Never use the current HEAD merely to make the historical diff empty. Existing scope revisions reject `--baseline-head` and always preserve their original baseline.

## Merge and verify

In `SUPERVISED`, record the user's exact approved PR and HEAD after the technical review gate:

```bash
python3 "$WORKFLOWCTL" approve --action merge --evidence 'user approval after review'
```

Then execute and verify the protected merge:

```bash
python3 "$WORKFLOWCTL" advance --to MERGE_READY
python3 "$WORKFLOWCTL" begin-merge
python3 "$WORKFLOWCTL" merge-record --merge-sha MERGE-SHA
python3 "$WORKFLOWCTL" advance --to MERGED
python3 "$WORKFLOWCTL" advance --to VERIFYING_DEVELOP
python3 "$WORKFLOWCTL" develop-verified \
  --merge-sha MERGE-SHA --remote-base-sha REMOTE-BASE-SHA \
  --evidence 'git ancestor verification'
python3 "$WORKFLOWCTL" advance --to POST_MERGE_MEMORY
python3 "$WORKFLOWCTL" memory-gate \
  --status PASS --file PATH/TO/PROJECT-MEMORY \
  --summary 'durable non-secret summary emitted' --secrets-check PASS
python3 "$WORKFLOWCTL" advance --to COMPLETED
```

Use `revoke-delegation` on user revocation, `scope-block` for ownership/dependency/WBS decisions, `block` only for genuine non-scope external blockers, and `batch-status` before declaring the batch closed.
