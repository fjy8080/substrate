---
name: amd-workflow-rules
description: AMD (Agent Managed Delivery) 工作流核心规则 — 每次开发会话必须遵循，除非用户明确切回 CCB
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-18T14:36:26.668Z
---

# AMD 工作流核心规则（默认工作流）

> **除非用户明确说"切回 CCB"，否则始终使用 AMD 工作流。**

## 一、根本原则

1. **不用 CCB**，用 AMD（`/agent-managed-delivery` skill）。
2. **必须开 subagent**：Main Agent 不亲自写代码，通过 Task Scout / Explorer / Developer / Knowledge Keeper / Reviewer / Utility 角色分工。
3. **串行业务任务**：即使有空闲 slot，业务任务也串行推进；只对独立只读调查做并行。
4. **Main Agent 拥有状态机**：负责 scope 解释、review 分诊、授权门禁、外部写入和最终事实声明。
5. **用 `workflowctl.py` 管理持久状态**：存在 `.git/agent-managed-delivery/state.json`（git common dir，跨 worktree 共享）。

## 二、状态机流程

```
CANDIDATE → CLAIMED → EXPLORING → DEVELOPING → SELF_TESTING → IMPLEMENTATION_READY_FOR_DOCS → DOCUMENTING → PR_CREATING → CI_PENDING → REVIEW_REQUESTED → REVIEWING → MERGE_READY → MERGING → MERGED → VERIFYING_DEVELOP → POST_MERGE_MEMORY → COMPLETED
```

辅助状态：`FIXING_CI`、`FIXING_REVIEW`、`SCOPE_BLOCKED`、`SERIOUSLY_BLOCKED`。

## 三、Subagent 角色与调度

| 角色 | 职责 | 能否写代码 |
|------|------|-----------|
| **Main Agent** | 状态机、scope 解释、review 分诊、授权门禁、外部写入 | 主控 |
| **Task Scout** | 侦察可用任务，推荐但不领取 | ❌ 只读 |
| **Explorer** | 映射代码、契约、测试、风险 | ❌ 只读 |
| **Developer** | 唯一代码写手（task worktree 内） | ✅ |
| **Knowledge Keeper** | 文档审计与记忆更新（Developer 停止后才能开始） | ✅ |
| **Reviewer** | 每轮全新只读上下文审查完整 diff | ❌ 只读 |
| **Utility** | 确定性只读命令与证据格式化 | ❌ 只读 |

**调度规则**：
- 禁止同一 worktree 内 Developer 和 Knowledge Keeper 并发写入。
- Reviewer 不能同时是 Developer。
- 第 1-3 轮 Review 修复 P0-P4；第 4 轮起只修复 P0/P1。

## 四、Scope 管理（关键）

- 开发前必须 `scope-record` 记录范围契约（WBS 来源、输出、验收、测试、允许路径）。
- 每次新 HEAD 必须 `scope-check`，范围外路径只能进入 `SCOPE_BLOCKED`。
- **`allowed-paths` 一次列全**，避免 scope 反复变更（历史教训：遗漏导致多次 scope-change）。
- 范围变更只能在 `SCOPE_BLOCKED` 状态由用户明确批准。

## 五、Review 与合并门禁

- Review 发现分为 `IN_SCOPE_DEFECT` / `PREDECESSOR_DEFECT` / `UNMERGED_DEPENDENCY` / `WBS_AMBIGUITY` / `FUTURE_WBS_GAP` / `HARDENING_SUGGESTION` 等。
- 严重度 P0-P4：P0/P1 可阻塞，P2-P4 第 4 轮起只做非阻塞观察。
- 合并必须保护 exact reviewed HEAD，禁止 admin bypass。
- 评论使用 `APPROVED_FOR_MERGE_BY_COMMENT`（普通评论批准），不得冒充平台 Approve。
- GitHub formal reviews = 0 是常见状态（comment-based approval），不等于没有审查。

## 六、授权模式

| 模式 | PR 创建 | 合并 | 范围变更 |
|------|---------|------|----------|
| **SUPERVISED** | 需用户批准 | 需用户批准 | 需用户批准 |
| **DELEGATED_BATCH** | 预授权自动 | 预授权自动 | 需用户批准 |

## 八、参考文件

- Skill 定义：`~/.claude/skills/agent-managed-delivery/SKILL.md`
- 状态机：`~/.claude/skills/agent-managed-delivery/references/state-machine.md`
- Subagent 调度：`~/.claude/skills/agent-managed-delivery/references/subagent-scheduling.md`
- 项目适配：`~/.claude/skills/agent-managed-delivery/references/project-adaptation.md`
- 实操约定（workaround）：见 [[amd-cc-workarounds]]
