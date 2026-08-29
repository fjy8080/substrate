#!/usr/bin/env node
/**
 * Claude Code Notification hook —— 收到通知事件时弹系统通知。
 * 跨平台：Linux(notify-send) / macOS(osascript) / Windows(PowerShell Toast)。
 * 由 ~/.claude/settings.json 的 hooks.Notification 调用，stdin 传入 hook JSON payload。
 * 安装位置：~/.claude/scripts/notification.js
 * 注意：统一使用 spawnSync + 参数数组，不经 shell 拼接，避免 payload 内容注入命令。
 */
'use strict';
const { spawnSync } = require('child_process');

const notify = (cmd, args) => {
  try {
    spawnSync(cmd, args, { stdio: 'ignore', timeout: 5000 });
  } catch (_) {
    /* 通知失败不影响 hook 本身 */
  }
};

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let title = 'Claude Code';
  let message = '需要你的注意（权限确认或空闲提醒）';
  try {
    const j = JSON.parse(raw);
    if (j.message) message = String(j.message);
    if (j.claude_title || j.title) title = String(j.claude_title || j.title);
  } catch (_) {
    /* payload 不是 JSON 时用默认文案 */
  }

  if (process.platform === 'linux') {
    notify('notify-send', ['-a', 'ClaudeCode', title, message]);
  } else if (process.platform === 'darwin') {
    notify('osascript', ['-e', `display notification ${JSON.stringify(message)} with title ${JSON.stringify(title)}`]);
  } else {
    notify('powershell', ['-NoProfile', '-Command',
      `New-BurntToastNotification -Text '${title.replace(/'/g, "''")}','${message.replace(/'/g, "''")}'`]);
  }
  process.exit(0);
});
