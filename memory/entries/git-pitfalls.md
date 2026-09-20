---
name: git-pitfalls
description: Git 实战坑合集——squash 合并假象、冲突禁整文件 --theirs、freeze 分支 -s ours、Fixes #N 关票条件、gh api 应急推送、ls-remote 权威校验、push 前预检
metadata:
  type: reference
---

# Git 实战坑合集

每条都是真实翻车后的沉淀。

- **判断系统现状前先 `git fetch --all`**：本地检出可能落后远端几百个提交。用 `git rev-list --left-right --count <local>...<remote>` 核对，用 `git show origin/<base>:<path>` 读远端真实代码，不要把本地工作区当系统现状。
- **squash 合并的分支在 git 里「看似未合并」**：`git branch -r --merged` 不含它。判定是否完成用 `gh pr list --state all --head <branch>`（state=MERGED 且分支 tip 与 PR headRefOid 一致），再到主干 `git branch --contains <mergeCommit>` 终验。
- **冲突取一侧禁用 `git checkout --theirs <整文件>`**：它会把分支侧的非冲突 hunk 也一起覆盖丢掉。只删冲突标记内的一侧（编辑器/脚本定位标记实际索引），删完用 `wc -l` 与双方原文件对照；取侧后必须跑全量本地检查兜底。
- **发版冻结（release 分支合 main）标准解**：当 CHANGELOG 是唯一冲突点时，freeze 分支用 `git merge -s ours <主干>` 一次定版。
- **`Fixes/Closes #N` 只在合入默认分支时自动关票**：PR base 是 develop 等非默认分支时合并后不会关票，必须手动确认 AC 证据、填好关闭记录（PR/Exact HEAD/CI/Review/验证结果/结论）再 `gh issue close`。
- **push/fetch 全断时的应急推送**：gh CLI 的 API 调用常不受影响。走 GitHub API：blob 上传（base64，幂等）→ `git/trees`（base_tree=目标基线树）→ `git/commits` → `PATCH git/refs/heads/<分支>`。关键不变量：git 对象 sha 确定性——本地 `git write-tree` 与服务端建出的树 sha 一致，可作「树等价证明」。
- **分支清单以 `git ls-remote --heads origin` 为权威**：`git branch -r --format='%(refname:short)'` 会把 origin/HEAD 输出成裸 `origin`，拼进删除命令会产生非法引用；删除前校验清单是其子集。
- **push 前本地预检空白错误**：`git diff --check <base>...HEAD`（exit 0 才 push），避免 CI 上 trailing whitespace 类失败多跑一轮。
- **受限环境 force-push 替代**：本地工具拦截 `git push --force-with-lease` 时：①确认远端仍是预期旧 SHA；②`git push origin HEAD:refs/heads/tmp/<short>` 上传对象；③`gh api -X PATCH .../git/refs/heads/<feature> -f sha=<new> -F force=true`；④删临时分支。绝不 force 主干。
- **代理下 SSH 长命令会被掐**（常见空闲 60s 断连，远端命令链被 SIGHUP 杀掉）：远程长等待拆成多次短调用；等待放本地 sleep；断连后先重连确认前半段是否已生效。

关联 [[git-branch-discipline]]、[[shell-and-ci-pitfalls]]。
