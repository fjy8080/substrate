---
name: codex-tmpfs-review-dirs
description: CCB/review 工作流在 /tmp 堆 review checkout+venv 会把 3.9G tmpfs 塞满，codex 配置是 Windows 迁移残留
metadata:
  type: project
---

/tmp 是 tmpfs(仅 3.9G)。用户的 CCB PR-review 工作流([[ssh-access-workflow]] 同环境)每次在 /tmp 建 repo checkout 和 venv(命名模式 `pr*`、`hxcq*`、`shenxue*`、`xingyan*`),一天能堆 2.9G+,把 /tmp 塞到 80%+ 触发 codex "配额满"弹窗。2026-08-28 已清理过一次。

~/.codex/config.toml 和 hooks.json 是从 Windows(旧机器,用户名不同)迁移来的，排查 codex 异常时优先找 `C:\Users\...` / `/c/Users/...` 残留路径(已修过 notify 和 check-memory-links 两处)。

**Why:** tmpfs 满会级联导致 npx/hook 等一切依赖 /tmp 的操作失败，报错看起来无关、根因在磁盘。
**How to apply:** /tmp 异常时先 `df -h /tmp`;清理用 `-mmin +120` 年龄过滤并让用户以 `!` 前缀自行执行(批量 rm -rf 会被权限拦截)。
