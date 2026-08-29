# Developer 请求审查评论模板

```md
## Developer：请求评论式审查

任务 `<TASK-ID>` 已完成开发、自测和项目文档更新。

- 当前 HEAD：`<FULL-HEAD-SHA>`
- 范围修订：`<SCOPE-REVISION>`
- exact-HEAD 范围检查：`PASS`
- PR 目标：`<BASE-BRANCH>`
- 本地验证：`PASS`
- 项目文档门禁：`PASS`
- PR 正文动态元数据：`PASS|NOT_REQUIRED`（已绑定当前 HEAD）
- Required CI：`PASS`
- 请求审查轮次：`<ROUND>`
- 本轮阻断阈值：`P0-P4|P0-P1`
- 已知限制：`<NONE-OR-DESCRIPTION>`
- 相邻 WBS 排除项：`<EXCLUSIONS>`
- 上轮差异（首轮填 `N/A`）：`<PRIOR-ROUND-DELTA>`

请 Reviewer 对当前 SHA 和相对于 `<BASE-BRANCH>` 的完整 diff 进行独立审查，并按已记录
范围报告观察。第 4 轮起聚焦 P0/P1，观察到的 P2-P4 只能作为非阻塞项。Reviewer 结论须
由 Main Agent 复现、分级和分诊后才能发布普通 PR 评论。

<!-- agent-event
schema: 1
actor: developer
event: REVIEW_REQUESTED
task_id: <TASK-ID>
head_sha: <FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION>
scope_check: PASS
review_round: <ROUND>
blocking_severities: [<P0, P1, P2, P3, P4|P0, P1>]
ci_result: PASS
docs_gate: PASS
pr_metadata: PASS|NOT_REQUIRED
-->
```
