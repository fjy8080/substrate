v1

## User Profile

The user works across multiple product projects and local tooling workflows. They use Codex for tightly scoped delivery, live GitHub/CI/Project verification, evidence-backed planning, and durable local handoffs. They set explicit worktree, allowed-path, publication, and merge boundaries and expect them to be followed literally. They sometimes run short terminal commands themselves via the REPL prefix.

## User preferences

- Respect explicit read-only, no-commit/push/PR/merge/publish, worktree, and allowed-path boundaries; do not infer broader authority.
- Ask directly instead of guessing: mark requirements/design as confirmed/pending/recommended and raise unresolved product or technical boundaries to the user.
- Treat “当前正在进行” Issues as a no-claim conflict list; inspect owner, open PR, file overlap, and live state before creating a worktree.
- For review-only work, use exact HEAD/three-dot diff and structured evidence; do not fix or publish findings unless authorized.
- With explicit batch authorization, automate review/comment publication; an explicit “不要合并” still forbids merging, even after a passing review.
- Fix CI before review: every HEAD change invalidates CI, review, and merge authorization; rebind the complete gate set.
- In AMD, Main orchestrates while Developer writes code; use independent review and preserve one Issue/worktree/PR at a time. Do not start AMD until explicitly invoked.
- For a narrow repair, fix only that; retain surrounding contracts, avoid opportunistic edits, and report exact validation outcomes and HEAD.
- Validate end-to-end behavior, not only configuration/listing; skipped Docker/browser tests are unverified gates, not passes.
- Preserve existing UI/layout and visually verify desktop changes; for user-run shell actions, provide short pasteable commands.

## General Tips

- Treat historical Issue/PR/Project/branch facts as routing leads only; refresh repo rules, exact HEAD, checks, mergeability, comments, dependencies, authorization, and worktree status.
- Docker/Testcontainers skips and local browser/integration limitations are unverified gates; report them separately from passing tests/CI.
- A formal GitHub APPROVE may need the user or explicit permission; a review comment/old CI/on-another-SHA result is not current approval.
- Batch GitHub evidence should be serial or small-batch with bounded retries; on EOF, ConnectionRefused, GraphQL errors, or incomplete snapshots, stop publication until exact-head evidence is complete.
- New DB migrations require a whole-tree scan for version/count/target assertions.
- Canonical project `memory/` may be an untracked symlink. Confirm its target and exact status before cleanup or post-merge updates.
- Never store or expose secrets. Search SSH configuration narrowly and exclude private keys; ignored `.env`/local settings do not belong in PRs.
