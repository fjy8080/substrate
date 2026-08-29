---
name: github-projects-api
description: GitHub Projects API 硬规则指针——权威全文在项目共享 memory/09-github-projects-api.md
metadata:
  node_type: memory
  type: reference
  modified: 2026-08-19T09:16:00.000Z
---

# GitHub Projects API（MEM-DEC-013）

权威全文在项目共享记忆 **`memory/09-github-projects-api.md`**，不要在本目录维护副本。

开工即生效：

1. 每个任务最多一次 Project 全量初始化读取。
2. 缓存 Project / Field / Option / Item ID；本任务禁止重复 discovery。
3. 只查完成当前任务所需字段；禁止拉 comments、reactions、历史等无关数据。
4. 禁止多个 Agent 并发 Project mutation。
5. 所有 Project 写操作进入单一串行队列。
6. Mutation 之间至少间隔 1 秒。
7. 多项修改先生成完整 diff，再集中执行；禁止「改一次 → 全量读取 → 再改一次」。
8. 全部 mutation 完成后最多一次统一验证。
9. 收到 403 / 429 / rate limit 时立即停止请求。
10. 优先遵守 Retry-After；否则 60 / 120 / 240 / 480 秒指数退避。
11. 禁止因 API 失败无限 retry。
12. 尽量使用已有 Issue / Project ID；禁止重复搜索同一资源。
