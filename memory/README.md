# memory —— 通用记忆包

跨项目沉淀的 agent 工作方法论，全部从真实项目实战中提炼。全部条目**宿主中立**：Claude Code、Codex、OpenCode 或任何能读 Markdown 的 agent 都可以直接使用。

## 目录

```
memory/
├── MEMORY.md      # 全部条目的索引（含一句话摘要）
├── entries/       # 通用方法论（宿主无关）
├── hosts/         # 宿主专属实操备忘（claude-code.md / codex.md）
└── codex-pack/    # Codex 原生格式的可部署记忆包（install.sh --with-memory 用）
```

## 使用方式

**方式一（推荐）：并入你项目的记忆体系**

1. 把需要的 `entries/*.md` 拷进目标项目的 memory 目录（或 home 级记忆目录，全局生效）；
2. 在该目录的 `MEMORY.md` 索引补一行 `- [标题](文件名.md) — 一句话钩子`；
3. 条目里的 `[[互链]]` 指向其他条目的 name，缺失的链接表示「值得补写」而不是错误。

**方式二：Codex 原生格式**

```bash
bash install.sh --with-memory --host codex   # 部署 codex-pack/ 到 ~/.codex/memories/
```

**方式三：项目内共享（多工具单一真相源）**

把 `entries/` 直接放进项目 `memory/` 目录，让所有 agent 工具共用——见 `entries/shared-memory-location.md` 与 `entries/project-memory-protocol.md`。

## frontmatter 约定

```yaml
---
name: kebab-case-slug        # 全局唯一，[[互链]] 用它指向
description: 一行摘要，用于判断相关性
metadata:
  type: reference | feedback # reference=怎么做的知识；feedback=行为纪律（含 Why/How to apply）
---
```

`type: feedback` 的条目正文遵循 **Why / How to apply** 结构：先讲为什么有这条纪律，再讲怎么落地。

## 收录标准

只收「对未来工作有用」的：决策与理由、坑与解法、稳定事实、可复用流程。不收过程性流水账；条目过期即删。
