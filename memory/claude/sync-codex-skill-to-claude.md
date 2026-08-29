---
name: sync-codex-skill-to-claude
description: 从 codex(~/.codex/skills) 同步 skill 修复到 claude(~/.claude/skills) 时必须回译的平台占位符与跳过项
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-02T18:16:47.251Z
---

用户在 codex(`~/.codex/skills/`) 与 claude(`~/.claude/skills/`) 两边维护同一套 5 个 skill（agent-managed-delivery / github-pr-fix / github-issue-debug / github-issue-create / github-pr-review）。codex 那边改了之后要同步到 claude 时，**不能整目录 cp**，必须区分「通用逻辑修复」与「codex 平台特有」。

**回译规则**（claude 侧套用 sed）：
- `$<skill>` → `/<skill>`（codex 用 `$` 前缀调用 skill，claude 用 `/`）
- `~/.codex/` → `~/.claude/`；`$HOME/.codex/` → `$HOME/.claude/`（注意两种写法都要覆盖）
- `<THIS-SKILL>` → `~/.claude/skills/<所属skill>`（codex skill 框架会展开此占位符，**claude 不展开**，留着会是字面量，必须写实绝对路径）
- `~/.codex/agents/` → `~/.claude/agents/`

**跳过项**（codex 平台特有，不同步进 claude skill）：
- 各 skill 内嵌的 `agents/openai.yaml`：claude 用全局 `~/.claude/agents/*.md`（见 [[subagent-model-opus-only]]），不内嵌
- `scripts/__pycache__/`：构建产物
- 纯平台差异无 bug 修复的 SKILL.md（用 `diff -u` 逐行确认是否含本次修复的逻辑；仅占位符差异、无实质内容差异的可跳过）

**实操手法**：纯逻辑文件（templates/references 中无占位符的、scripts/.py）直接 `cp` 覆盖；含占位符的文件（通常是 SKILL.md + commands.md）`cp` 后 sed 批量回译。三处 `sync_pr_metadata.py` md5 一致、纯 stdlib+subprocess 调 gh，可放心 cp。

**验证**：`grep -rnE '\$agent-managed-delivery|\$github-...|~/\.codex|<THIS-SKILL>' ~/.claude/skills/` 应空（跳过的旧 skill 本就没这些）；跑 `python3 .../scripts/test_*.py`；`diff` 复查回译文件只剩占位符分歧。

**Why**: codex 与 claude 的 skill 框架在调用前缀、路径、占位符展开、agent 定义位置上都有差异，照搬会让 claude 侧出现字面 `<THIS-SKILL>`、`$skill` 等失效内容。

相关:[[subagent-model-opus-only]]
