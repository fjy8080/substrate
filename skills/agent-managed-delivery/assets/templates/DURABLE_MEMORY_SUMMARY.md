# 可沉淀记忆摘要模板（宿主通用）

任务合并并验证后，在当前会话向用户输出以下摘要；宿主具备持久记忆机制时（如 Codex memories、
Claude Code auto-memory、项目内 memory 目录），同时把该摘要落入对应的记忆位置：

```md
### Durable project memory

项目 `<PROJECT>` 的任务 `<TASK-ID>` 已通过 PR #<NUMBER> 合并到 `<BASE-BRANCH>`，merge commit 为 `<FULL-SHA>`。最终实现了：<FINAL-BEHAVIOR>。以后处理相关代码时必须遵守：<DURABLE-CONSTRAINTS>。关键决策：<DECISIONS>。已知限制：<LIMITATIONS>。相关项目文档已更新：<DOCS>. 不包含任何 secrets。
```

该摘要用于让具备记忆机制的会话具备可沉淀材料；不得声称后台 memory 文件已经即时刷新。
