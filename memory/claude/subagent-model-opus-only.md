---
name: subagent-model-opus-only
description: 用户要求 Claude Code 自定义 subagent 全部用 opus，不要按原档位降级到 haiku/sonnet
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-02T12:50:24.409Z
---

用户明确要求：agent-managed-delivery 的全部 subagent（task-scout / workflow-explorer / workflow-developer / knowledge-keeper / workflow-reviewer / workflow-utility）`model` 字段统一用最强档位（opus），不做降级映射。

**Why:** 用户更看重 subagent 的能力与质量，不愿为了省 token/延迟而用弱模型担当 subagent 角色。

**How to apply:** 为该用户配置任何自定义 subagent（`~/.claude/agents/*.md` 或项目级 `.claude/agents/`）时，`model` 默认填 `opus`，除非用户明确另行指定。注意：若角色定位是「低成本/廉价」（如 utility），改 opus 后描述文案里的 low-cost / cheap 字样会与 model 语义冲突，应一并调整描述。
