---
name: git-branch-discipline
description: 本项目 Git 关键纪律——本地根分支长期落后、必须从最新 origin/develop 建独立 worktree、remote 实际名 origin、不自行合并
metadata: 
  node_type: memory
  type: project
  originSessionId: 943cecdc-2688-4c81-96c2-f7cb6cce66fb
  modified: 2026-08-03T16:06:21.051Z
---

深学AI 项目 Git 工作流的关键、易踩坑点（项目 `memory/03` 与 `AGENTS.md §4` 为权威，此处只记 Claude Code 视角下最易出错的稳定约束；具体落后数/PR/HEAD 请实时核对，不在此维护）。

- **remote 实际名为 `origin`**（不是旧历史记录里的 `upstream`）；开工前 `git remote -v` 复核。
- **本地根工作区长期落后**：项目 `memory/01` 多次记录根工作区停在旧的本地 `develop@4225445`、落后 `origin/develop` 数十个提交、且未快进。**下一项实际开发必须从最新 `origin/develop` 创建独立 worktree；不得在根目录快进、也不得从旧本地基线开工。** 落后数使用前必须重新核对。
- 分支命名 `feature/i{迭代号}-{描述性英文名}`；**一任务一分支一 PR**；多任务并行用独立 worktree，禁止跨分支夹带改动。
- 不直接在 `main`/`develop` 上开发或推送。
- 实现者**不自行合并 PR**：普通任务至少 1 名未参与实现者审查；鉴权/合规/迁移/文件安全/AI 真值/恢复等高风险任务需 2 名独立审查人。
- 禁止未经确认的 `reset --hard`、强推、清空卷等高风险操作。

具体当前 PR/Gate 状态请查项目 `memory/01`。关联 [[shared-memory-location]]。
