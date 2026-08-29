---
name: subagent-model-opus-only
description: 用户要求 Claude Code 自定义 subagent 全部用 opus，不要按原档位降级到 haiku/sonnet
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c239b16a-5e08-41a4-aab4-3aa79290cc21
  modified: 2026-08-02T12:50:24.409Z
---

用户明确要求：从 codex 迁移到 Claude Code 的 6 个 agent-managed-delivery subagent（task-scout / workflow-explorer / workflow-developer / knowledge-keeper / workflow-reviewer / workflow-utility）的 `model` 字段全部设为 `opus`，不按 codex 原模型档位（luna→haiku、terra→sonnet、sol→opus）做降级映射。

**Why:** 用户更看重 subagent 的能力与质量，不愿为了省 token/延迟而用弱模型担当 subagent 角色。

**How to apply:** 为该用户配置任何自定义 subagent（`~/.claude/agents/*.md` 或项目级 `.claude/agents/`）时，`model` 默认填 `opus`，除非用户明确另行指定。注意：若角色定位是「低成本/廉价」（如 utility），改 opus 后描述文案里的 low-cost / cheap 字样会与 model 语义冲突，应一并调整描述。
