# 严重阻塞评论模板

```md
## Agent Workflow：严重阻塞

- 任务：`<TASK-ID>`
- 当前状态：`<STATE>`
- 当前 HEAD：`<SHA-OR-NONE>`
- 阻塞类型：`<TYPE>`
- 事实证据：<EVIDENCE>
- 已尝试动作：<ATTEMPTS>
- 为什么无法安全继续：<REASON>
- 所需解阻条件：<UNBLOCK-CONDITION>
- 对其他任务的影响：<IMPACT>

<!-- agent-event
schema: 1
actor: main
event: SERIOUS_BLOCKER_RECORDED
task_id: <TASK-ID>
blocker_type: <TYPE>
-->
```
