'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');
const { recordDecision } = require('../src/runtime-audit.cjs');

const repositoryRoot = path.join(__dirname, '..');

function temporaryDirectory(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'sts-cli-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  return directory;
}

function run(args) {
  return spawnSync(process.execPath, ['scripts/sts.cjs', ...args], {
    cwd: repositoryRoot,
    encoding: 'utf8'
  });
}

test('doctor, runtime, explain, and label expose the local evidence chain', (t) => {
  const dataDir = temporaryDirectory(t);
  const event = recordDecision({
    sessionId: 'session-secret',
    controlState: 'armed',
    action: { name: 'apply_patch', mutability: 'write', affectedPaths: ['secret.txt'] },
    contract: { mode: 'review', level: 'guard', agentBudget: 0, agentsUsed: 0, hashPolicy: 'deny', dependencyPolicy: 'ask', allowedPaths: [] },
    decision: { outcome: 'deny_and_explain', family: 'I', reasonCode: 'MODE_FORBIDS_MUTATION' },
    responseOutcome: 'permission_deny_returned'
  }, { dataDir });

  const doctor = run(['doctor', '--data-dir', dataDir]);
  assert.equal(doctor.status, 0, doctor.stderr);
  assert.equal(JSON.parse(doctor.stdout).runtimeLogFiles, 1);

  const runtime = run(['runtime', '--data-dir', dataDir]);
  assert.equal(runtime.status, 0, runtime.stderr);
  assert.equal(JSON.parse(runtime.stdout).summary.permissionDenyResponses, 1);

  const explain = run(['explain', event.eventId, '--data-dir', dataDir]);
  assert.equal(explain.status, 0, explain.stderr);
  assert.equal(JSON.parse(explain.stdout).event.eventId, event.eventId);

  const label = run(['label', event.eventId, 'correct', '--data-dir', dataDir]);
  assert.equal(label.status, 0, label.stderr);
  assert.equal(JSON.parse(label.stdout).label, 'correct');
});

test('case new creates a deliberately incomplete reviewable skeleton', (t) => {
  const root = temporaryDirectory(t);
  const output = path.join(root, 'sample');
  const created = run(['case', 'new', '--id', 'sample', '--output', output]);
  assert.equal(created.status, 0, created.stderr);
  assert.equal(fs.existsSync(path.join(output, 'case.json')), true);

  const validation = run(['case', 'validate', output]);
  assert.equal(validation.status, 1);
  assert.match(validation.stderr, /privacy|acceptance|sanitized/i);
});
