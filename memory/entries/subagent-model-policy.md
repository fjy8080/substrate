---
name: subagent-model-policy
description: 自定义 subagent 统一用最强可用模型档位，不做降级映射——质量优先于 token 成本
metadata:
  type: feedback
---

# Subagent 模型档位策略

配置任何自定义 subagent 时，`model` 字段默认填宿主可用的**最强档位**（如 Claude Code 的 opus），不做「按角色降级到弱模型」的映射，除非用户明确指定降级。

**Why:** subagent 承担的是独立调查、实现与审查职责，能力与质量直接决定交付质量；为省 token/延迟而用弱模型担当 subagent 角色得不偿失。

**How to apply:** 写 subagent 定义（如 `~/.claude/agents/*.md` 或项目级 `.claude/agents/`）时统一最强档位。注意：若角色定位是「低成本/廉价」（如 utility），改强模型后描述文案里的 low-cost / cheap 字样会与 model 语义冲突，应一并调整描述。
