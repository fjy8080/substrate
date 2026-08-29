# Reviewer 允许合并评论模板

```md
## Agent Review：允许合并

- 任务：`<TASK-ID>`
- 范围修订：`<SCOPE-REVISION>`
- 审查轮次：`<ROUND>`
- 审查 SHA：`<FULL-HEAD-SHA>`
- Required CI：`PASS`
- 项目文档门禁：`PASS`
- PR 正文动态元数据：`PASS|NOT_REQUIRED`
- 本轮阻断阈值：`P0-P4|P0-P1`
- 当前范围内、符合阈值的阻断问题：`0`
- 结论：`APPROVED_FOR_MERGE_BY_COMMENT`

### 范围审计

- WBS 独立输出与验收：<WBS-BASIS>
- 当前 diff 涉及路径/能力：<DIFF-SCOPE>
- 相邻 WBS 排除项：<ADJACENT-WBS-EXCLUSIONS>
- 与上一轮差异（首轮填 `N/A`）：<PRIOR-ROUND-DELTA>

### 分诊结果

| 分类 | 数量 | 处理 |
|---|---:|---|
| `IN_SCOPE_DEFECT`（符合本轮阈值） | 0 | 无 |
| `IN_SCOPE_DEFECT`（第 4 轮起 P2-P4） | <N> | 已验证并作为非阻塞项留档，不再修复 |
| `PREDECESSOR_DEFECT/UNMERGED_DEPENDENCY/WBS_AMBIGUITY`（第 4 轮起 P2-P4） | <N> | 归属相邻任务，非阻塞留档 |
| `FUTURE_WBS_GAP` | <N> | 延后到对应 WBS，不阻塞 |
| `HARDENING_SUGGESTION` | <N> | 建议项，不阻塞 |
| `NOT_REPRODUCIBLE/ALREADY_FIXED/INVALID` | <N> | 已记录证据 |

本轮严重度可阻塞的 `PREDECESSOR_DEFECT`、`UNMERGED_DEPENDENCY`、`WBS_AMBIGUITY` 和
P0/P1 `FUTURE_WBS_GAP` 均为 0。第 4 轮起如有 P2-P4 范围观察，已在上表中注明归属且不阻塞。

本评论只表示当前范围和 exact HEAD 的技术审查通过。`SUPERVISED` 模式仍须等待用户批准合并；`DELEGATED_BATCH` 模式仅在已明确授予 merge 权限时才可继续。

<!-- agent-review
schema: 3
verdict: APPROVED_FOR_MERGE_BY_COMMENT
task_id: <TASK-ID>
review_round: <ROUND>
reviewed_head_sha: <FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION>
blocking_findings: 0
in_scope_blocking_findings: 0
blocking_severities: [<P0, P1, P2, P3, P4|P0, P1>]
deferred_non_blocking_findings: <N>
deferred_scope_findings: <N>
deferred_scope_finding_ids: [<ID>]
scope_blocking_findings: 0
predecessor_defects: <N>
unmerged_dependencies: <N>
future_wbs_gaps: <N>
wbs_ambiguities: <N>
hardening_suggestions: <N>
ci_result: PASS
docs_gate: PASS
pr_metadata: PASS|NOT_REQUIRED
merge_target: <BASE-BRANCH>
-->
```
