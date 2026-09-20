---
name: session-handoff-discipline
description: 会话交接纪律——只要开了 PR/推了分支，即使任务中断也必须把分支/PR/基线/状态写进任务记忆
metadata:
  type: feedback
---

# 会话交接纪律

**只要开了 PR 或推了分支，即使任务中断，也要在会话结束前把「分支名 / PR 号 / 基线 / 状态 / 下一步」写进任务记忆（tasks.md 或同等位置）。**

**Why:** 真实事故：上个会话凌晨开了 3 个 PR、推了实现分支，结束前没写记忆；新会话按记忆盘点「可做项」时差点重复开票撞文件——半成品记录比没有记录更关键，因为下一个会话最先做的事就是「避开在办」。

**How to apply:**

- 会话结束前的固定动作：盘点本次会话产生的所有远程痕迹（分支、PR、issue 认领、看板状态），逐条写入任务记忆。
- 接手会话的盘点三件套（快速核对在办、发现记忆断层）：`gh pr list --state open` + `git ls-remote origin | grep <关键词>` + 看板状态，三者交叉才能发现「有分支没 PR」「有 PR 没进记忆」这类断层。
- 记忆里记状态快照时同时记「核对命令」，让下一个会话能一键验证快照是否仍然成立。

关联 [[project-memory-protocol]]、[[multi-agent-task-claiming]]。
