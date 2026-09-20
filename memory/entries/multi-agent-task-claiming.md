---
name: multi-agent-task-claiming
description: 多人/多 agent 仓库的任务认领协议——认领前五查、领取即占坑、归属只认 commit author、对他人产物禁令、误操作撤出流程
metadata:
  type: feedback
---

# 多 agent 任务认领协议

多人/多 agent 协作的仓库里，撞车的代价是整批作废。任何批次/任务开工前强制执行以下流程。

**Why:** 真实事故：把他人挂在看板上的在办任务误判为「无主欠账」，开了 5 任务批次后整体撞车作废，对远程的更改全部撤销。

## 第一步：认领前五查（全部通过才可开工）

1. `gh issue view <N> --json assignees` —— 已被 assign（给任何人）→ 不碰，除非用户明确协调；
2. 项目看板该 issue 的 Status —— `In progress`/`In review` → 有人在办，不碰；
3. `git ls-remote origin | grep <分支关键词>` —— 远端已有对应分支 → 有人在推进，不碰；
4. `gh pr list --state open` —— 已有关联 PR → 不碰；
5. 判断产物归属**只认 commit author 账号**（`git log --format='%an'`），不认「PR 是谁开的」「分支在不在远端」——owner 开的 PR 可能装着别人的提交。本地记忆快照可能滞后，一切以 GitHub live 为准。

## 第二步：领取即占坑（查完无人认领后立即做，再开始探索/开发）

- `gh issue edit <N> --add-assignee <自己账号>`；
- 看板状态置 In progress；开 PR 后同步更新看板。
- 不占坑 = 别人无从知道你在做，撞车是对等的。

## 第三步：对他人产物的禁令

- 不 rebase / force-push / 改正文 / 改看板状态任何属于他人的 PR、分支与 issue；
- 发现他人 PR 的问题 → 整理证据交给用户（或 issue 评论走该仓库的审查协议），不直接动手修。

## 第四步：误操作撤出流程（万一对远程做了更改）

- 撤自己混入别人分支的提交：`git rebase --onto <对方前一提交> <我的提交> <分支>` + `git push --force-with-lease=refs/heads/<分支>:<远端当前SHA> origin <分支>`（**必须 force-with-lease，绝不裸 --force**；重写后提醒对方 `git pull --rebase` 对齐）；
- 恢复被覆盖的 PR 正文：用保存的原文 `gh pr edit --body-file` 还原，再同步机器可校验的元数据；
- 删自己的评论 / 孤儿 CI run：`gh api -X DELETE .../issues/comments/<id>`、`gh run delete <id>`；
- 无法撤销的残留（正文编辑历史、对方 SHA 被重写）必须明示给用户。

关联 [[session-handoff-discipline]]、[[github-projects-api]]。
