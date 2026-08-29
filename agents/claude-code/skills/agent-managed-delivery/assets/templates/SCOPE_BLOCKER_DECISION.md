# 范围阻塞决策包模板

当出现 `PREDECESSOR_DEFECT`、`UNMERGED_DEPENDENCY`、`WBS_AMBIGUITY`，或继续修复需要改变
WBS 所有权时使用。此模板请求决策，不是修复指令或 PR verdict。

```md
## Agent Workflow：等待范围/WBS 决策

- 任务：`<TASK-ID>`
- 当前状态：`SCOPE_BLOCKED`
- 当前 HEAD：`<FULL-HEAD-SHA>`
- 当前范围修订：`<SCOPE-REVISION-OR-NONE>`
- 阻塞类别：`PREDECESSOR_DEFECT|UNMERGED_DEPENDENCY|WBS_AMBIGUITY|SCOPE_EXPANSION_REQUIRED`

### 已确认事实

- 复现或权威证据：<EVIDENCE>
- 已完成的安全调查：<INVESTIGATION>
- 当前任务 WBS 依据：<CURRENT-WBS-BASIS>
- 相关前置/后续任务及实时状态：<DEPENDENCY-STATUS>
- 为什么不属于普通当前任务修复：<OWNERSHIP-ANALYSIS>

### 有界选项

1. <OPTION-1-AND-IMPACT>
2. <OPTION-2-AND-IMPACT>

### 请求用户执行

<WAIT/COORDINATE/REJECT-FINDING/EXPLICITLY-APPROVE-SCOPE-REVISION>

在用户明确决定前不继续编码、不修改 WBS、不向 Developer 派发该问题。

<!-- agent-event
schema: 1
actor: main
event: SCOPE_BLOCKED_DECISION_REQUESTED
task_id: <TASK-ID>
head_sha: <FULL-HEAD-SHA>
scope_revision: <SCOPE-REVISION-OR-NONE>
blocker_category: <CATEGORY>
-->
```
