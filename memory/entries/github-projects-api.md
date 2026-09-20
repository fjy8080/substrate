---
name: github-projects-api
description: GitHub Projects（GraphQL）API 硬规则——限流退避、单写队列、禁并发 mutation、禁止无限重试
metadata:
  type: reference
---

# GitHub Projects API 硬规则

操作 GitHub Projects（GraphQL API）时开工即生效：

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

查询/修改 PR/Issue 同理：尽量批量操作，不要频繁并发小查询；在 main agent 内通过一次 `gh` 调用获取多个 PR/Issue 的状态，而非逐个查询。
