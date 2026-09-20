---
name: worktree-tips
description: git worktree 实操技巧——软链共享 node_modules/.venv/memory、.gitignore 斜杠与软链的坑、跑完删链再提交
metadata:
  type: reference
---

# git worktree 实操技巧

多任务并行时每个 worktree 都是独立目录，依赖与本地配置不共享，用软链解决：

- **前端 node_modules**：软链主仓的 `node_modules` 到 worktree 对应目录即可跑 vitest/tsc/build（store 命中时 install 也很快）。**跑完删软链再 commit**。
- **后端 venv**：共享 venv 实体可放任一 worktree，其余软链过去（untracked，不进 commit，scope diff 不受影响）。cwd 决定 import 哪份代码（非 editable-install），跑测试必须 `cd <worktree>/<包目录>`。
- **项目本地 memory**：git-ignored 的项目 `memory/` 只在主工作区存在；worktree 里建软链 `ln -sfn <主工作区>/memory <worktree>/memory` 即可通过需要该路径的 gate 检查。
- **worktree 里软链 gitignored 依赖**（如 `backend/.env → ../.env`）：软链本身可能不被 `.gitignore` 规则覆盖——`**/.venv/` 带斜杠只匹配目录，不匹配软链。提交前 `git status` 核对，跑完删除。
- **worktree 的 git 状态在 common dir**：所有 worktree 共享 `.git`（common dir），跨 worktree 持久状态文件放 `.git/<name>/`（如 agent-managed-delivery 的 state.json）即可全局共享、不产生 tracked 文件。

关联 [[git-branch-discipline]]、[[hosts-claude-code]]（沙箱 cwd 限制下的 GIT_DIR 变通）。
