#!/usr/bin/env node

const { handleHook } = require('../src/hook-policy.cjs');

function readStdin(maxWaitMs = 1500) {
  return new Promise((resolve) => {
    let settled = false;
    let body = '';

    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(body);
    };

    const timer = setTimeout(finish, maxWaitMs);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      body += chunk;
    });
    process.stdin.on('end', finish);
    process.stdin.on('error', finish);
    process.stdin.resume();
  });
}

(async () => {
  try {
    const raw = await readStdin();
    if (!raw.trim()) return;

    const input = JSON.parse(raw);
    const output = handleHook(input);
    if (output) {
      process.stdout.write(`${JSON.stringify(output)}\n`);
    }
  } catch (error) {
    const errorName = error && error.name ? error.name : 'HookError';
    process.stderr.write(`Stop That Shit hook failed open: ${errorName}\n`);
  }
})();
