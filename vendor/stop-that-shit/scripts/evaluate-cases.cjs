#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');
const { decide } = require('../src/decision.cjs');

const root = path.join(__dirname, '..', 'cases', '0.0.1');
const files = fs.readdirSync(root).filter((name) => name.endsWith('.json')).sort();
let failures = 0;

for (const file of files) {
  const testCase = JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
  const actual = decide(testCase.input);
  const pass = Object.entries(testCase.expected).every(([key, value]) => actual[key] === value);
  if (!pass) failures += 1;
  process.stdout.write(`${pass ? 'PASS' : 'FAIL'} ${testCase.id} ${actual.outcome} ${actual.family || '-'}\n`);
}

process.stdout.write(`\n${files.length - failures}/${files.length} paired-case arms passed.\n`);
process.exitCode = failures ? 1 : 0;
