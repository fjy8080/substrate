'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { defaultContract } = require('./contracts.cjs');

function dataRoot(override) {
  return override || process.env.PLUGIN_DATA || process.env.CLAUDE_PLUGIN_DATA || path.join(os.tmpdir(), 'stop-that-shit-dev');
}

function sessionKey(sessionId) {
  return crypto.createHash('sha256').update(String(sessionId || 'unknown')).digest('hex').slice(0, 24);
}

function statePath(sessionId, override) {
  return path.join(dataRoot(override), 'sessions', `${sessionKey(sessionId)}.json`);
}

function freshState() {
  return {
    schemaVersion: 1,
    contract: defaultContract(),
    lastPromptContext: null
  };
}

function readState(sessionId, override) {
  const file = statePath(sessionId, override);
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
    return {
      ...freshState(),
      ...parsed,
      contract: { ...defaultContract(), ...(parsed.contract || {}) }
    };
  } catch (error) {
    if (error && (error.code === 'ENOENT' || error.name === 'SyntaxError')) return freshState();
    throw error;
  }
}

function writeState(sessionId, state, override) {
  const file = statePath(sessionId, override);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(state, null, 2)}\n`, { encoding: 'utf8', mode: 0o600 });
  try {
    fs.renameSync(temporary, file);
  } catch (error) {
    if (process.platform !== 'win32') throw error;
    fs.copyFileSync(temporary, file);
    fs.unlinkSync(temporary);
  }
}


function lockPath(sessionId, override) {
  return `${statePath(sessionId, override)}.lock`;
}

function sleepSync(milliseconds) {
  const shared = new Int32Array(new SharedArrayBuffer(4));
  Atomics.wait(shared, 0, 0, milliseconds);
}

function acquireSessionLock(sessionId, override, options = {}) {
  const file = lockPath(sessionId, override);
  const timeoutMs = Number.isFinite(options.timeoutMs) ? options.timeoutMs : 1500;
  const staleMs = Number.isFinite(options.staleMs) ? options.staleMs : 10000;
  const started = Date.now();
  fs.mkdirSync(path.dirname(file), { recursive: true });

  while (true) {
    try {
      const fd = fs.openSync(file, 'wx', 0o600);
      const token = `${process.pid}:${crypto.randomUUID()}`;
      fs.writeFileSync(fd, `${token} ${Date.now()}\n`, 'utf8');
      return () => {
        try { fs.closeSync(fd); } catch {}
        try {
          const owner = fs.readFileSync(file, 'utf8').trim().split(/\s+/, 1)[0];
          if (owner === token) fs.unlinkSync(file);
        } catch (error) {
          if (!error || error.code !== 'ENOENT') throw error;
        }
      };
    } catch (error) {
      if (!error || error.code !== 'EEXIST') throw error;
      try {
        const stat = fs.statSync(file);
        if (Date.now() - stat.mtimeMs > staleMs) {
          fs.unlinkSync(file);
          continue;
        }
      } catch (statError) {
        if (statError && statError.code === 'ENOENT') continue;
        throw statError;
      }
      if (Date.now() - started >= timeoutMs) {
        const timeout = new Error(`Timed out waiting for Stop That Shit session lock: ${sessionKey(sessionId)}`);
        timeout.code = 'STS_LOCK_TIMEOUT';
        throw timeout;
      }
      sleepSync(10);
    }
  }
}

function withSessionLock(sessionId, override, fn, options) {
  const release = acquireSessionLock(sessionId, override, options);
  try {
    return fn();
  } finally {
    release();
  }
}

module.exports = {
  acquireSessionLock,
  dataRoot,
  freshState,
  readState,
  sessionKey,
  statePath,
  withSessionLock,
  writeState
};
