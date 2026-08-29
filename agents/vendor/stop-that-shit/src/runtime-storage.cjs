'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { dataRoot } = require('./state.cjs');

function runtimeRoot(options = {}) {
  const root = options.dataDir || process.env.STS_RUNTIME_DATA || dataRoot();
  return path.join(root, 'runtime');
}

function appendJsonl(file, record) {
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  fs.appendFileSync(file, `${JSON.stringify(record)}\n`, { encoding: 'utf8', mode: 0o600 });
}

function readJsonl(file) {
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') return { records: [], damaged: 0 };
    throw error;
  }

  const records = [];
  let damaged = 0;
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      records.push(JSON.parse(line));
    } catch {
      damaged += 1;
    }
  }
  return { records, damaged };
}

module.exports = { appendJsonl, readJsonl, runtimeRoot };
