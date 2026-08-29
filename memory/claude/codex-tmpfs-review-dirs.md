---
name: codex-tmpfs-review-dirs
description: review 工作流在 /tmp 堆 checkout+venv 塞满 tmpfs 的排查手法；迁移/复用配置的路径残留警惕
metadata:
  type: project
---

/tmp 是 tmpfs(仅 3.9G)。用户的 CCB PR-review 工作流([[ssh-access-workflow]] 同环境)每次在 /tmp 建 repo checkout 和 venv(按 PR/项目名命名的目录),一天能堆数 G,把 /tmp 塞到 80%+ 触发 "配额满"弹窗。

迁移/复用来的 codex 配置(config.toml、hooks.json)可能含旧平台的绝对路径(`C:\Users\...`、`/c/Users/...`),排查 codex hook 异常时优先检索这类残留路径。

**Why:** tmpfs 满会级联导致 npx/hook 等一切依赖 /tmp 的操作失败，报错看起来无关、根因在磁盘。
**How to apply:** /tmp 异常时先 `df -h /tmp`;清理用 `-mmin +120` 年龄过滤并让用户以 `!` 前缀自行执行(批量 rm -rf 会被权限拦截)。
