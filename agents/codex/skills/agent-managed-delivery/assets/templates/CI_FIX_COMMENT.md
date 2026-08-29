# CI 修复说明评论模板

```md
## Developer：CI 问题已修复

- 任务：`<TASK-ID>`
- 范围修订：`<SCOPE-REVISION>`
- 失败检查：`<CHECK-NAME>`
- 根因：<ROOT-CAUSE>
- 修复：<FIX>
- 当前 HEAD：`<FULL-HEAD-SHA>`
- 本地复现与验证：`PASS`
- exact-HEAD 范围检查：`PASS`
- 项目文档重新审计：`PASS|NOT_AFFECTED`
- PR 正文动态元数据：`PASS|NOT_REQUIRED`（exact-HEAD 回读）
- Required CI：`PASS`

<!-- agent-event
schema: 1
actor: developer
event: CI_FIX_PUSHED
task_id: <TASK-ID>
head_sha: <FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION>
scope_check: PASS
ci_result: PASS
docs_gate: PASS
pr_metadata: PASS|NOT_REQUIRED
-->
```
