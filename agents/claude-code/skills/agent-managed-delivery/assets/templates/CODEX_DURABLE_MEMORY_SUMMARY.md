# Codex 可沉淀记忆摘要模板

任务合并并验证后，在当前 Codex 会话输出：

```md
### Durable project memory

项目 `<PROJECT>` 的任务 `<TASK-ID>` 已通过 PR #<NUMBER> 合并到 `<BASE-BRANCH>`，merge commit 为 `<FULL-SHA>`。最终实现了：<FINAL-BEHAVIOR>。以后处理相关代码时必须遵守：<DURABLE-CONSTRAINTS>。关键决策：<DECISIONS>。已知限制：<LIMITATIONS>。相关项目文档已更新：<DOCS>. 不包含任何 secrets。
```

该摘要用于让启用 memories 的 Codex 会话具备可沉淀材料；不得声称后台 memory 文件已经即时刷新。
