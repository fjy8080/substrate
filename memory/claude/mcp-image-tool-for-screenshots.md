---
name: mcp-image-tool-for-screenshots
description: 用户附截图时用 MCP 图像工具读取，别因内置 Read 返回 unsupported 就放弃
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3b56bc05-d12e-46c4-acf3-fddb2a7a4c9f
  modified: 2026-08-02T16:20:50.100Z
---

用户在消息里附带本地截图/图片时，内置 Read 工具可能返回 `[Unsupported Image]`；应改用 MCP 图像分析工具读取：

- `mcp__zai-mcp-server__analyze_image`（`image_source` 支持本地文件路径，通用图像分析）
- `mcp__zai-mcp-server__ui_to_artifact`（UI 截图专用，`output_type='description'` 生成自然语言描述）
- `mcp__4_5v_mcp__analyze_image` 仅支持远程 URL，本地文件不要用这个

**Why:** 用户期望充分利用已接入的 MCP 工具。本次报 UI 溢出 bug 时，我因 Read 返回 `[Unsupported Image]` 就声明"未臆造截图、以代码核查为准"，被用户提醒"你不是有 MCP 工具可以读取图片吗"。事后用 `analyze_image` 成功读到界面细节（当前 tab、被截断的区域、表格列），与代码根因交叉互证，证据链才闭环。

**How to apply:** 用户消息含本地图片且 Read 失败时，立即调用 MCP 图像工具（UI 截图优先 `ui_to_artifact`/`analyze_image`），prompt 聚焦与当前任务相关的视觉细节（布局/溢出/报错/可见文字）；把读到的客观内容与代码核查交叉互证，不臆造看不到的部分。参见 [[subagent-model-opus-only]]（核查类 subagent 同样用 opus）。
