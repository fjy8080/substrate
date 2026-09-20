# Developer 修复说明评论模板

```md
## Developer：审查问题已修复

- 任务：`<TASK-ID>`
- 范围修订：`<SCOPE-REVISION>`
- 上一轮：`<PREVIOUS-ROUND>`
- 当前 HEAD：`<NEW-FULL-HEAD-SHA>`

### 逐项处理

| Finding ID | 分诊类别 | 严重度 | 状态 | 修改位置 | 验证方式 |
|---|---|---|---|---|---|
| `<ID>` | `IN_SCOPE_DEFECT` | `P0|P1|P2|P3|P4` | 已修复 | `<PATH>` | `<TEST>` |

只列出主 Agent 派发的本轮阻断项。第 4 轮起不得接收或顺手修复 P2-P4，相关观察只留在
Reviewer 的非阻塞区。

- Repair whitelist：`<EXACT-BLOCKING-FINDING-IDS>`
- 实际回报 ID：`<EXACT-SAME-FINDING-IDS>`
- Changed capabilities：`<CAPABILITY-LIST>`
- 白名单外能力/非阻塞项修改：`NONE`

### 本轮验证

- 本地编译：`PASS`
- 自动化测试：`PASS`
- exact-HEAD 范围检查：`PASS`
- 项目文档重新审计：`PASS`
- PR 正文动态元数据：`PASS|NOT_REQUIRED`（`base=<BASE> / commits=<N> / files=<N>`，已回读）
- Required CI：`PASS`

本次 Push 已使上一轮审查结论失效。现请求 Reviewer 对最新 SHA 进行完整复审。

<!-- agent-event
schema: 1
actor: developer
event: REVIEW_FIXES_PUSHED
task_id: <TASK-ID>
head_sha: <NEW-FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION>
scope_check: PASS
review_fix_record: PASS
resolved_findings:
  - <ID>
next_review_round: <NEXT-ROUND>
ci_result: PASS
docs_gate: PASS
pr_metadata: PASS|NOT_REQUIRED
-->
```
