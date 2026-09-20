# Issue 模板要点

起草 Issue 时的结构性要点（配套仓库 `templates/github/ISSUE_TEMPLATE/` 的完整模板；目标仓库有自己的模板时以它的为准）。

## 结构骨架

1. **观察事实先于根因推测**：问题描述区只写「用户看到了什么、影响谁」；根因假设放在独立段落并显式标注为假设。
2. **当前行为 + 证据**：发现基线（commit/版本）、证据链接（日志/CI/截图，脱敏）、是否回归。
3. **In scope / Out of scope**：显式圈定本 Issue 修复什么、不修什么——防修复时范围膨胀。
4. **追溯字段**：Owning Task（任务编号）、依赖、Contract impact 三值（`NONE` / `IMPLEMENT_EXISTING` / `CHANGE_REQUIRES_DECISION`）、权威文档与章节。未知填「待确认」，不虚构。
5. **验收标准（AC）必须可验证**：写「执行 X 后可观察到 Y」，给出可量化判定；不写「功能完成」「体验更好」这类不可验证表述。
6. **关闭记录段**（由验证人填写）：PR、Exact HEAD、CI、Review、验证结果、结论（CLOSED/REOPEN）——让每个 Issue 的关闭有完整证据链。

## 关联语义

- `Fixes/Closes #N` 只在合入**默认分支**时自动关票；base 为其他分支时合并后必须手动关闭并填关闭记录。
- 仅引用背景用 `Refs #N`。
