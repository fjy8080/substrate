#!/usr/bin/env node

'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const {
  buildCodexArgs,
  buildPlan,
  assertNoAgentInstructions,
  assertInstalledPluginMatchesSource,
  assertIsolatedPluginList,
  assertWorkspaceRootIsolated,
  evaluateAcceptance,
  isSuccessfulSummary,
  materializeFixture,
  repositoryRevision,
  resolveCodexInvocation,
  rescoreRun,
  resultStatus,
  summarizeResults
} = require('./paired-eval-lib.cjs');
const { readRuntime } = require('../src/runtime-audit.cjs');
const packageJson = require('../package.json');

const root = path.resolve(__dirname, '..');
const evalRoot = path.join(root, 'evals', 'codex-paired');

function parseArgs(argv) {
  const options = {
    dryRun: true,
    runs: 3,
    cases: [],
    arms: [],
    caseDirectories: [],
    model: null,
    reasoning: null,
    maxCells: null,
    rescore: null,
    allowAcceptanceCommands: false,
    dangerFullAccess: false,
    timeoutMs: 600_000,
    codexHome: process.env.STS_EVAL_CODEX_HOME || null,
    workspaceRoot: process.env.STS_EVAL_WORKSPACE_ROOT
      || path.join(os.tmpdir(), 'stop-that-shit-eval-workspaces')
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--run') options.dryRun = false;
    else if (arg === '--dry-run') options.dryRun = true;
    else if (arg === '--runs') options.runs = Number(argv[++index]);
    else if (arg === '--case') options.cases.push(argv[++index]);
    else if (arg === '--arm') options.arms.push(argv[++index]);
    else if (arg === '--case-dir') options.caseDirectories.push(argv[++index]);
    else if (arg === '--model') options.model = argv[++index];
    else if (arg === '--reasoning') options.reasoning = argv[++index];
    else if (arg === '--max-cells') options.maxCells = Number(argv[++index]);
    else if (arg === '--rescore') options.rescore = argv[++index];
    else if (arg === '--allow-acceptance-commands') options.allowAcceptanceCommands = true;
    else if (arg === '--danger-full-access') options.dangerFullAccess = true;
    else if (arg === '--codex-home') options.codexHome = argv[++index];
    else if (arg === '--workspace-root') options.workspaceRoot = argv[++index];
    else if (arg === '--timeout-ms') options.timeoutMs = Number(argv[++index]);
    else if (arg === '--help' || arg === '-h') options.help = true;
    else throw new Error(`unknown argument: ${arg}`);
  }
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1) {
    throw new Error('timeout-ms must be a positive integer');
  }
  if (options.reasoning && !/^[a-z][a-z0-9_-]*$/i.test(options.reasoning)) {
    throw new Error('reasoning must be a simple level name');
  }
  if (options.maxCells !== null && (!Number.isInteger(options.maxCells) || options.maxCells < 1)) {
    throw new Error('max-cells must be a positive integer');
  }
  return options;
}

function usage() {
  return [
    'Usage: node scripts/run-paired-eval.cjs [--dry-run] [--run] [options]',
    '',
    'The default is --dry-run. --run starts paid Codex sessions.',
    '',
    'Options:',
    '  --runs <n>       Repetitions per case and arm (default: 3)',
    '  --case <id>      Select a family or full case id; repeatable',
    '  --case-dir <p>   Load one external CaseBundle v1 directory; repeatable',
    '  --arm <id>       Select baseline, instruction, or plugin; repeatable',
    '  --rescore <p>    Recompute acceptance from one archived run without Codex',
    '  --allow-acceptance-commands  Permit reviewed command checks during rescore',
    '  --model <id>     Pin the Codex model (required with --run)',
    '  --reasoning <n>  Pin reasoning effort (required with --run)',
    '  --max-cells <n>  Hard paid-session cap (required with --run)',
    '  --danger-full-access  Disable the Codex sandbox for disposable fixtures only',
    '  --codex-home <p> Dedicated authenticated Codex home with only this plugin enabled',
    '  --workspace-root <p> External root for isolated live workspaces',
    '  --timeout-ms <n> Timeout for each Codex session'
  ].join('\n');
}

function filterPlan(plan, options) {
  const cells = plan.cells.filter((cell) => {
    const caseMatch = options.cases.length === 0
      || options.cases.includes(cell.family)
      || options.cases.includes(cell.caseId);
    const armMatch = options.arms.length === 0 || options.arms.includes(cell.arm);
    return caseMatch && armMatch;
  });
  if (cells.length === 0) throw new Error('the selected matrix is empty');
  const caseIds = new Set(cells.map((cell) => cell.caseId));
  const armIds = new Set(cells.map((cell) => cell.arm));
  return {
    ...plan,
    arms: plan.arms.filter((arm) => armIds.has(arm.id)),
    cases: plan.cases.filter((testCase) => caseIds.has(testCase.id)),
    cells
  };
}

function findCodexInvocation() {
  if (process.env.STS_CODEX_BIN) {
    const configured = path.resolve(process.env.STS_CODEX_BIN);
    return configured.toLowerCase().endsWith('.js')
      ? { command: process.execPath, argsPrefix: [configured] }
      : { command: configured, argsPrefix: [] };
  }
  const lookup = process.platform === 'win32'
    ? spawnSync('where.exe', ['codex'], { encoding: 'utf8' })
    : spawnSync('which', ['codex'], { encoding: 'utf8' });
  if (lookup.status !== 0) throw new Error('codex CLI was not found on PATH');
  const candidates = lookup.stdout.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
  return resolveCodexInvocation(candidates);
}

function runCodex(invocation, args, options) {
  return spawnSync(invocation.command, [...invocation.argsPrefix, ...args], options);
}

function preflightEvalHome(invocation, codexHome) {
  if (!codexHome) {
    throw new Error('--codex-home or STS_EVAL_CODEX_HOME is required with --run');
  }
  const resolved = path.resolve(codexHome);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
    throw new Error(`eval Codex home is not a directory: ${resolved}`);
  }
  const env = { ...process.env, CODEX_HOME: resolved };
  const login = runCodex(invocation, ['login', 'status'], { encoding: 'utf8', env });
  if (login.status !== 0) {
    const detail = login.error ? ` (${login.error.code || login.error.message})` : '';
    throw new Error(`the isolated eval Codex home is not authenticated${detail}`);
  }
  const plugins = runCodex(invocation, ['plugin', 'list'], { encoding: 'utf8', env });
  if (plugins.status !== 0) {
    throw new Error(plugins.stderr || 'could not list plugins in the isolated eval Codex home');
  }
  assertIsolatedPluginList(plugins.stdout);
  const pluginCache = assertInstalledPluginMatchesSource(root, resolved, packageJson.version);
  const version = runCodex(invocation, ['--version'], { encoding: 'utf8', env });
  return { codexHome: resolved, pluginCache, env, codexVersion: version.status === 0 ? version.stdout.trim() : 'unknown' };
}

function finalResponse(eventsText) {
  let response = '';
  for (const line of eventsText.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const event = JSON.parse(line);
      if (event.type === 'item.completed' && event.item && event.item.type === 'agent_message') {
        response = event.item.text || response;
      }
    } catch {}
  }
  return response;
}

function runCell(invocation, cell, options, evalProfile) {
  const workspace = path.join(options.workspaceRoot, cell.workspace);
  const outputDirectory = path.join(evalRoot, path.dirname(cell.workspace));
  const archivedWorkspace = path.join(evalRoot, cell.workspace);
  const runtimeData = path.join(outputDirectory, 'audit');
  try {
    materializeFixture(cell.fixtureDirectory || cell.fixture, workspace);
    fs.mkdirSync(outputDirectory, { recursive: true });
    const args = buildCodexArgs(cell, {
      model: options.model,
      reasoning: options.reasoning,
      workspace,
      dangerFullAccess: options.dangerFullAccess
    });
    const startedAt = Date.now();
    const execution = runCodex(invocation, args, {
      cwd: workspace,
      encoding: 'utf8',
      timeout: options.timeoutMs,
      maxBuffer: 32 * 1024 * 1024,
      env: { ...evalProfile.env, STS_RUNTIME_DATA: runtimeData }
    });
    const durationMs = Date.now() - startedAt;
    const eventsText = execution.stdout || '';
    const responseText = finalResponse(eventsText);
    const acceptance = evaluateAcceptance({
      workspace,
      acceptance: cell.acceptance,
      responseText,
      eventsText
    });
    const runtime = readRuntime({}, { dataDir: runtimeData }).summary;
    const executionFacts = {
      exitStatus: execution.status,
      signal: execution.signal,
      spawnError: execution.error ? execution.error.message : null
    };
    const result = {
      schemaVersion: 1,
      id: cell.id,
      caseId: cell.caseId,
      family: cell.family,
      kind: cell.kind,
      arm: cell.arm,
      run: cell.run,
      prompt: cell.prompt,
      environment: {
        codexVersion: evalProfile.codexVersion,
        model: options.model,
        reasoning: options.reasoning,
        platform: process.platform,
        architecture: process.arch,
        sandbox: options.dangerFullAccess ? 'danger-full-access' : 'workspace-write',
        pluginVersion: packageJson.version,
        pluginRevision: evalProfile.pluginRevision
      },
      ...executionFacts,
      durationMs,
      runtime,
      acceptance
    };
    result.status = resultStatus(result, acceptance);
    fs.writeFileSync(path.join(outputDirectory, 'events.jsonl'), eventsText, 'utf8');
    fs.writeFileSync(
      path.join(outputDirectory, 'stderr.txt'),
      execution.stderr || (execution.error ? `${execution.error.stack || execution.error.message}\n` : ''),
      'utf8'
    );
    fs.writeFileSync(path.join(outputDirectory, 'result.json'), `${JSON.stringify(result, null, 2)}\n`, 'utf8');
    fs.cpSync(workspace, archivedWorkspace, { recursive: true });
    return result;
  } finally {
    fs.rmSync(workspace, { recursive: true, force: true });
  }
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  if (options.rescore) {
    process.stdout.write(`${JSON.stringify(rescoreRun(options.rescore, {
      allowAcceptanceCommands: options.allowAcceptanceCommands
    }), null, 2)}\n`);
    return;
  }
  const plan = filterPlan(buildPlan({ runs: options.runs, caseDirectories: options.caseDirectories }), options);
  if (options.dryRun) {
    process.stdout.write(`${JSON.stringify(plan, null, 2)}\n`);
    return;
  }

  if (!options.codexHome) {
    throw new Error('--codex-home or STS_EVAL_CODEX_HOME is required with --run');
  }
  if (!options.model) {
    throw new Error('--model is required with --run so result bundles identify the evaluated model');
  }
  if (!options.reasoning) {
    throw new Error('--reasoning is required with --run so result bundles identify the reasoning effort');
  }
  if (options.maxCells === null) {
    throw new Error('--max-cells is required with --run');
  }
  if (plan.cells.length > options.maxCells) {
    throw new Error(`selected matrix has ${plan.cells.length} cells, above --max-cells ${options.maxCells}`);
  }
  const invocation = findCodexInvocation();
  const evalProfile = preflightEvalHome(invocation, options.codexHome);
  evalProfile.pluginRevision = repositoryRevision(root);
  options.workspaceRoot = assertWorkspaceRootIsolated(root, options.workspaceRoot);
  assertNoAgentInstructions(options.workspaceRoot);
  assertNoAgentInstructions(evalProfile.codexHome, { ancestors: false });
  if (options.dangerFullAccess) {
    process.stderr.write('WARNING danger-full-access is enabled for disposable eval fixtures\n');
  }
  const runRoot = path.join(evalRoot, 'runs', plan.stamp);
  fs.mkdirSync(runRoot, { recursive: true });
  fs.writeFileSync(path.join(runRoot, 'plan.json'), `${JSON.stringify(plan, null, 2)}\n`, 'utf8');
  const results = [];
  for (const cell of plan.cells) {
    process.stderr.write(`RUN ${cell.id}\n`);
    const result = runCell(invocation, cell, options, evalProfile);
    results.push(result);
    process.stderr.write(`${result.acceptance.pass ? 'PASS' : 'FAIL'} ${cell.id}\n`);
  }
  const summary = summarizeResults(results, { planned: plan.cells.length });
  fs.writeFileSync(path.join(runRoot, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
  if (!isSuccessfulSummary(summary)) process.exitCode = 1;
}

try {
  main();
} catch (error) {
  process.stderr.write(`paired eval failed: ${error.message}\n`);
  process.exitCode = 1;
}
