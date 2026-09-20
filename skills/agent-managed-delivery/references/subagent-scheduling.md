# Subagent scheduling

Use available concurrency, not a hard-coded assumed count. The Main Agent remains active and owns the state machine.

Roles:

- Task Scout: read-only task and dependency reconnaissance.
- Explorer: read-only code, contract, test, and impact mapping.
- Developer: sole code writer in the task worktree.
- Knowledge Keeper: documentation/memory writer after Developer stops.
- Reviewer: fresh read-only context for every review round.
- Utility: deterministic read-only commands and evidence formatting.

Scheduling rules:

1. Keep business tasks serial even when more agent slots exist.
2. Parallelize only independent read-only investigations that materially reduce latency.
3. Allow one writer per worktree. Never overlap Developer and Knowledge Keeper writes.
4. Do not give Reviewer Developer self-evaluation or hidden reasoning. Provide the raw task, recorded scope manifest, adjacent WBS ownership, live dependency status, rules, diff, exact HEAD, CI, and authoritative documents.
5. Require Reviewer to identify the reproduction and likely WBS ownership of every finding. Reviewer may flag a cross-task risk but may not label it a current blocker merely because it is real or severe.
6. A Reviewer context cannot become the Developer for its own findings. Return raw findings to Main
   for independent reproduction, severity assignment, and `review-triage`; send Developer only
   severity-eligible `IN_SCOPE_DEFECT` findings. Rounds 1-3 allow P0-P4; round 4 onward allows only
   P0/P1 and leaves P2-P4 as non-blocking observations.
7. If Main classifies a severity-eligible finding as `PREDECESSOR_DEFECT`,
   `UNMERGED_DEPENDENCY`, or `WBS_AMBIGUITY`, do not schedule Developer. Enter `SCOPE_BLOCKED` and
   request the user's decision. From round 4 onward, P2-P4 instances are deferred unless the proven
   impact makes current P0/P1 acceptance impossible.
8. Do not start the next business task while CI, review, or a recoverable scope decision is pending for the current task.
9. Respect the runtime's actual subagent limit. If the source design requests more slots than available, reduce parallel read-only work and report the compatibility difference.
