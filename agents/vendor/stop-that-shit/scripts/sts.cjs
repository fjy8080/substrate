#!/usr/bin/env node

'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const packageJson = require('../package.json');
const { readRuntime } = require('../src/runtime-audit.cjs');
const { recordAnnotation } = require('../src/runtime-annotations.cjs');
const { validateCaseBundle } = require('./case-bundle-lib.cjs');

const root = path.resolve(__dirname, '..');

function parseArgs(argv) {
  const positional = [];
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--data-dir') options.dataDir = argv[++index];
    else if (value === '--id') options.id = argv[++index];
    else if (value === '--output') options.output = argv[++index];
    else positional.push(value);
  }
  return { positional, options };
}

function defaultCodexHome() {
  return process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
}

function resolveDataDir(explicit) {
  if (explicit) return path.resolve(explicit);
  if (process.env.STS_RUNTIME_DATA) return path.resolve(process.env.STS_RUNTIME_DATA);
  if (process.env.PLUGIN_DATA) return path.resolve(process.env.PLUGIN_DATA);
  return path.join(defaultCodexHome(), 'plugins', 'data', 'stop-that-shit-stop-that-shit');
}

function print(value) {
  process.stdout.write(`${typeof value === 'string' ? value : JSON.stringify(value, null, 2)}\n`);
}

function doctor(dataDir) {
  const runtimeDir = path.join(dataDir, 'runtime');
  const files = fs.existsSync(runtimeDir)
    ? fs.readdirSync(runtimeDir).filter((name) => name.endsWith('.jsonl'))
    : [];
  return {
    schemaVersion: 1,
    pluginVersion: packageJson.version,
    dataDir,
    dataDirExists: fs.existsSync(dataDir),
    runtimeLogFiles: files.filter((name) => name !== 'annotations.jsonl').length,
    annotationsPresent: files.includes('annotations.jsonl'),
    privacy: 'metadata-only/local-only',
    hostEffect: 'unobserved'
  };
}

function newCase(id, output) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id || '')) throw new Error('--id must be a lowercase slug');
  const target = path.resolve(output || path.join(root, 'evals', 'codex-paired', 'cases', id));
  if (fs.existsSync(target)) throw new Error(`CaseBundle target already exists: ${target}`);
  for (const kind of ['bad', 'good']) {
    fs.mkdirSync(path.join(target, 'fixtures', kind), { recursive: true });
    fs.writeFileSync(path.join(target, 'fixtures', kind, '.gitkeep'), '');
  }
  const manifest = {
    schemaVersion: 1,
    id,
    title: 'TODO: paired case title',
    provenance: { kind: 'community', source: 'TODO: sanitized source', sanitized: false },
    privacyReview: { confirmed: false },
    variants: {
      bad: {
        id: `${id}-bad`, title: 'TODO: Bad Case', contract: 'review',
        task: 'TODO: exact sanitized task', fixture: 'fixtures/bad', acceptance: []
      },
      good: {
        id: `${id}-good`, title: 'TODO: Good Case', contract: 'change',
        task: 'TODO: exact sanitized task with one changed fact', fixture: 'fixtures/good', acceptance: []
      }
    }
  };
  fs.writeFileSync(path.join(target, 'case.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  return { schemaVersion: 1, created: target, valid: false, next: 'Add sanitized fixtures and deterministic acceptance, then confirm privacyReview.' };
}

function main() {
  const { positional, options } = parseArgs(process.argv.slice(2));
  const [command, subcommand, ...rest] = positional;
  const dataDir = resolveDataDir(options.dataDir);

  if (command === 'doctor') return print(doctor(dataDir));
  if (command === 'runtime') return print(readRuntime({}, { dataDir }));
  if (command === 'explain') {
    const runtime = readRuntime({ eventId: subcommand }, { dataDir });
    if (runtime.events.length === 0) throw new Error(`runtime event not found: ${subcommand}`);
    return print({ schemaVersion: 1, event: runtime.events[0], annotations: runtime.annotations });
  }
  if (command === 'label') {
    const runtime = readRuntime({ eventId: subcommand }, { dataDir });
    if (runtime.events.length === 0) throw new Error(`runtime event not found: ${subcommand}`);
    const annotation = recordAnnotation(subcommand, rest[0], { dataDir });
    if (!annotation) throw new Error('could not append annotation');
    return print(annotation);
  }
  if (command === 'case' && subcommand === 'new') return print(newCase(options.id, options.output));
  if (command === 'case' && subcommand === 'validate') {
    const directory = rest[0];
    if (!directory) throw new Error('case validate requires a directory');
    const bundle = validateCaseBundle(directory);
    return print({ schemaVersion: 1, valid: true, id: bundle.id, cases: bundle.cases.map((entry) => entry.id) });
  }
  throw new Error([
    'Usage:',
    '  npm run sts -- doctor [--data-dir <path>]',
    '  npm run sts -- runtime [--data-dir <path>]',
    '  npm run sts -- explain <eventId> [--data-dir <path>]',
    '  npm run sts -- label <eventId> correct|incorrect|inconclusive [--data-dir <path>]',
    '  npm run sts -- case new --id <slug> [--output <path>]',
    '  npm run sts -- case validate <directory>'
  ].join('\n'));
}

try {
  main();
} catch (error) {
  process.stderr.write(`sts failed: ${error.message}\n`);
  process.exitCode = 1;
}
