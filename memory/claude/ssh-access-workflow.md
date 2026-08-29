---
name: ssh-access-workflow
description: 本机 ~/.ssh 对 Claude 的 Bash 是禁访的；需用户用 ! 前缀自跑短命令（长命令会被终端折行弄坏）
metadata:
  type: project
---

在这台机器上，我（Claude）通过 Bash 访问 `~/.ssh` 的任何形式（ls/cat/find）都会被权限设置拒绝，不要反复尝试。需要读 SSH 私钥/配置时，让用户用 `!` 前缀自己跑命令。

**Why:** 权限层明确拦截 ~/.ssh；且用户的终端会把超过约 120 字符的 `!` 命令折行，换行落在语法中间（如 `case "$f"` 与 `in` 之间）会导致 zsh 解析错误、整条命令不执行。

**How to apply:** 给用户的 `!` 命令务必短（一行内）；太长就写成脚本文件放到桌面让用户跑 `! ~/Desktop/xx.sh && rm ~/Desktop/xx.sh`。用户更偏好直观的短命令，而非脚本间接层。写敏感文件到桌面后顺手 `chmod 600`。
