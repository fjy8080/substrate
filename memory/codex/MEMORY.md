# Codex 全局记忆（脱敏精选版）

> 2026-08-30 从原机 `~/.codex/memories/MEMORY.md`（91KB / 19 个 Task Group）脱敏整理入库：
> - 已移除全部项目交付快照（shenxue-ai / HXCQ-Sport / xingyan 等 16 个 Task Group）及其中的业务实现细节
> - 已移除基础设施、服务器、代理工具链、本地系统操作与法律事务等敏感段落
> - 用户主目录路径统一写为 `~`（通用表述，不绑定具体用户名）
>
> 真正跨项目有价值的部分保留在 [memory_summary.md](memory_summary.md)（用户偏好 + 通用技巧）。
> 原始完整版只保留在原机，不在本仓库维护。

# Task Group: PDF answer highlighting

scope: Highlight answers in supplied Chinese practice PDFs while preserving originals and accurately reporting partial completion.
applies_to: cwd=~/Documents/Codex/2026-08-26/b; reuse_rule=file set and completion state are task-specific.

## Task 1: Two-PDF yellow highlighting, partial completion

### rollout_summary_files

- rollout_summaries/2026-08-26T01-30-06-OdYx-pdf.md (cwd=~/Desktop/project/shenxue-260-step3-markdown, rollout_path=~/.codex/sessions/2026/08/26/rollout-2026-08-26T09-30-06-01a03bb0-5371-7052-b054-06097091363d.jsonl, updated_at=2026-08-26T01:59:22+00:00, thread_id=01a03bb0-5371-7052-b054-06097091363d, partial)

### keywords

- PDF, 黄色高亮, 多选题, 跨行长选项, 输出目录, 83页, 8页

## User preferences

- the user requested “答案都用黄色高亮标记”, preserve originals, and place outputs separately. [Task 1]

## Reusable knowledge

- Highlight answer lines and all correct multi-select options, including cross-line long options. Only the 83-page PDF had completion evidence. [Task 1]

## Failures and how to do differently

- Do not imply the second 8-page PDF was delivered. [Task 1]
