# Reviewer 发现当前范围缺陷评论模板

仅在分诊后至少有一个“本轮严重度可阻塞的 `IN_SCOPE_DEFECT`”且没有严重度可阻塞的
范围阻塞类别时使用本模板。第 1-3 轮阈值为 P0-P4；第 4 轮起仅为 P0/P1。

```md
## Agent Review：当前范围需要修复

- 任务：`<TASK-ID>`
- 范围修订：`<SCOPE-REVISION>`
- 审查轮次：`<ROUND>`
- 审查 SHA：`<FULL-HEAD-SHA>`
- Required CI：`PASS`
- 项目文档门禁：`PASS|FAIL`
- PR 正文动态元数据：`PASS|NOT_REQUIRED`
- 结论：`CHANGES_REQUIRED_BY_COMMENT`
- 本轮阻断阈值：`P0-P4|P0-P1`

### 当前任务阻断问题

#### `<FINDING-ID>`｜`IN_SCOPE_DEFECT`｜`<SEVERITY>`

- 文件与位置：`<PATH:LINE-OR-SYMBOL>`
- 复现证据：<REPRODUCTION>
- 问题与影响：<PROBLEM-AND-IMPACT>
- 当前任务必须修复：<REQUIRED-FIX>
- WBS/范围依据：<OWNED-OUTPUT-OR-ACCEPTANCE-BASIS>

### 范围审计

- 当前 diff 路径/能力：<DIFF-SCOPE>
- 相邻 WBS 排除项：<ADJACENT-WBS-EXCLUSIONS>
- 与上一轮差异（首轮填 `N/A`）：<PRIOR-ROUND-DELTA>

### 延后或非阻断观察

| Finding ID | 分类 | 严重度 | 归属依据 | 后续去向 |
|---|---|---|---|---|
| `<ID>` | `IN_SCOPE_DEFECT|PREDECESSOR_DEFECT|UNMERGED_DEPENDENCY|FUTURE_WBS_GAP|WBS_AMBIGUITY|HARDENING_SUGGESTION|NOT_REPRODUCIBLE|ALREADY_FIXED|INVALID` | `P2|P3|P4|NA` | <BASIS> | <OWNER-OR-RECORD> |

本轮只要求 Developer 修复上方符合阈值的 `IN_SCOPE_DEFECT`。第 4 轮起，P2-P4 即使属于
当前任务也只保留在本表，不进入修复队列。如果出现本轮严重度可阻塞的前置缺陷、未合入
依赖、P0/P1 future gap 或 WBS 歧义，停止使用本模板并提交范围阻塞决策包。

<!-- agent-review
schema: 3
verdict: CHANGES_REQUIRED_BY_COMMENT
task_id: <TASK-ID>
review_round: <ROUND>
reviewed_head_sha: <FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION>
blocking_findings: <IN-SCOPE-COUNT>
in_scope_blocking_findings: <IN-SCOPE-COUNT>
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
finding_ids:
  - <IN-SCOPE-FINDING-ID>
repair_whitelist:
  - <BLOCKING-IN-SCOPE-FINDING-ID>
pr_metadata: PASS|NOT_REQUIRED
-->
```
