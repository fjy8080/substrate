---
name: project-memory-protocol
description: 项目记忆协议——六类分类、写入时机触发器（决策/踩坑立即写）、条目写「为什么」、记忆与代码冲突以代码为准
metadata:
  type: reference
---

# 项目记忆协议

给项目维护本地 `memory/` 目录时（工具无关，任何 agent 共用）遵循。

## 分类（六类）

| 文件 | 记什么 |
|---|---|
| `project.md` | 项目概况、稳定事实（README/docs 没写的） |
| `decisions.md` | 已锁定的决策与理由 |
| `conventions.md` | 协作约定与流程（多人/多 agent 规则） |
| `lessons.md` | 踩坑与解法 |
| `tasks.md` | 进行中任务的状态（分支/PR/基线/下一步） |
| `user.md` | 用户偏好与工作习惯 |

## 会话开始（读取记忆）

读 `memory/README.md`（索引），再按需读分类文件；涉及具体任务时至少读 project / conventions / tasks。

## 写入时机（触发器——立即写，不等会话结束）

- 做出了影响后续工作的决策 → `decisions.md`
- 踩坑并找到原因/解法 → `lessons.md`
- 发现了文档里没有的项目事实 → `project.md`
- 任务状态变化（开始/暂停/完成）→ `tasks.md`
- 用户表达了新的偏好或工作习惯 → `user.md`

## 条目格式与纪律

- 每条一个条目，带日期，一句话标题，**新条目加在文件顶部**：
  ```markdown
  ## YYYY-MM-DD — 一句话标题
  - 正文：事实/结论/原因。写「为什么」，不要只写「改了什么」。
  ```
- 只记**对未来工作有用**的信息：决策与理由、坑与解法、稳定的事实。不记过程性流水账（改了哪个文件、跑了什么命令）。
- **记忆与代码冲突时，以代码为准**，并顺手修正过期的记忆条目。
- 记忆条目过期即删除，保持每个文件精炼。
- 项目记忆目录通常 git-ignored（本地共享）；若工具在 worktree 里工作，见 [[worktree-tips]] 的软链做法。

关联 [[shared-memory-location]]、[[session-handoff-discipline]]。
