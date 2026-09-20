# 单任务状态记录模板

```yaml
task_id: <TASK-ID>
task_name: <NAME>
claimed_by_user: true
status: <STATE>
branch: <BRANCH>
base_branch: <BASE-BRANCH>
pr_number: <NUMBER-OR-NULL>
head_sha: <SHA-OR-NULL>
scope_revision: <N-OR-NULL>
scope_baseline_head_sha: <SHA-OR-NULL>
scope_check: PASS|BLOCKED|PENDING
scope_changed_paths: []
scope_drift_triggers: []
review_round: <N>
blocking_severities: [<P0, P1, P2, P3, P4|P0, P1>]
docs_gate: PASS|FAIL|PENDING
pr_metadata: PASS|NOT_REQUIRED|FAIL|PENDING
pr_metadata_head_sha: <SHA-OR-NULL>
pr_metadata_evidence: <READBACK-OR-CONTRACT-AUDIT>
ci_result: PASS|FAIL|PENDING|MISSING|CANCELLED
latest_review_verdict: <VERDICT-OR-NULL>
reviewed_head_sha: <SHA-OR-NULL>
blocking_findings: []
deferred_non_blocking_findings: []
deferred_scope_findings: []
finding_severity_counts:
  P0: 0
  P1: 0
  P2: 0
  P3: 0
  P4: 0
  NA: 0
finding_category_counts:
  IN_SCOPE_DEFECT: 0
  PREDECESSOR_DEFECT: 0
  UNMERGED_DEPENDENCY: 0
  FUTURE_WBS_GAP: 0
  WBS_AMBIGUITY: 0
  HARDENING_SUGGESTION: 0
scope_blocker: null
review_fix_authorization: null
review_fix_record: null
review_fix_history: []
merge_commit: <SHA-OR-NULL>
merge_verified_in_base: false
project_memory_updated: false
durable_memory_summary_emitted: false
serious_blocker: null
```
