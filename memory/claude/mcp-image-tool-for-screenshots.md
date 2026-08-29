---
name: mcp-image-tool-for-screenshots
description: 用户附截图时用 MCP 图像工具读取，别因内置 Read 返回 unsupported 就放弃
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-08-02T16:20:50.100Z
---

用户在消息里附带本地截图/图片时，内置 Read 工具可能返回 `[Unsupported Image]`；应改用 MCP 图像分析工具读取：

- `mcp__zai-mcp-server__analyze_image`（`image_source` 支持本地文件路径，通用图像分析）
- `mcp__zai-mcp-server__ui_to_artifact`（UI 截图专用，`output_type='description'` 生成自然语言描述）
- 仅支持远程 URL 的图像 MCP 工具不要用于本地文件

**Why:** 内置 Read 可能读不了本地截图；MCP 图像工具能读到布局、截断区域、表格列等客观细节，与代码核查交叉互证才能闭环证据链。

**How to apply:** 用户消息含本地图片且 Read 失败时，立即调用 MCP 图像工具（UI 截图优先 `ui_to_artifact`/`analyze_image`），prompt 聚焦与当前任务相关的视觉细节（布局/溢出/报错/可见文字）；把读到的客观内容与代码核查交叉互证，不臆造看不到的部分。参见 [[subagent-model-opus-only]]（核查类 subagent 同样用 opus）。
