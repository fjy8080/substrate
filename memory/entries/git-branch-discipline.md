---
name: git-branch-discipline
description: Git 关键纪律——remote 名实时复核、从最新 origin 基线建独立 worktree、一任务一分支一 PR、实现者不自行合并、禁高风险操作
metadata:
  type: feedback
---

# Git 分支纪律

agent 视角下最易出错的稳定约束（各项目以自己的 AGENTS.md 与 memory 为权威，具体状态实时核对，不在此维护）。

- **remote 名以 `git remote -v` 实时复核为准**，勿凭记忆或旧记录假设（常见为 `origin`）。
- **本地根工作区可能长期落后**：根工作区常停在旧的本地基线、落后 `origin` 基线多个提交且未快进。实际开发必须从最新 `origin/<base>` 创建独立 worktree；不得在根目录快进，也不得从旧本地基线开工。落后数使用前必须重新核对。
- **一任务一分支一 PR**；多任务并行用独立 worktree，禁止跨分支夹带改动。分支命名按项目约定（如 `feature/<scope>-<desc>`、`fix/issue-<number>-<desc>`），无约定时用描述性英文。
- 不直接在主干分支（`main`/`develop`）上开发或推送。
- 合并后删除远端 feature 分支，定期 `git remote prune`。
- **实现者不自行合并 PR**：普通任务至少 1 名未参与实现者审查；鉴权/合规/迁移/文件安全/AI 真值/恢复等高风险任务需 2 名独立审查人。
- 禁止未经用户确认的 `reset --hard`、强推、清空卷等高风险操作。

关联 [[shared-memory-location]]、[[git-pitfalls]]。
