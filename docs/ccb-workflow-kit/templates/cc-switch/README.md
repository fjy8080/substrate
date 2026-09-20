# cc-switch：只提供安全使用说明

cc-switch 是可选的本机账户/模型切换工具，不是 CCB 所必需的组件。本模板没有提供“真实配置文件”，这是刻意的：此类工具的数据库、备份、日志及账户切换信息可能包含可复用的登录态或 provider 凭据。

安全做法：

1. 同事在自己的设备安装 cc-switch，并用自己的账号完成设置。
2. 仅在本机 UI 中添加账号/模型；不导出数据库，不通过微信、网盘、Git 或压缩包传递。
3. CCB 遇到 provider 登录问题时，优先在该 provider 的正常 CLI 中登录；不要让 cc-switch 的内部文件成为 CCB 配置依赖。
4. 若不需要多账号切换，完全不安装 cc-switch；CCB、Codex、Claude Code 和 OpenCode 仍能正常协作。

绝不共享：`~/.cc-switch/`、任何 SQLite/DB 文件、日志、备份、账号导出、Cookie、token 或密钥。
