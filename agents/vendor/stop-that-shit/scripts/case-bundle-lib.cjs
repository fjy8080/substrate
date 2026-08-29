'use strict';

const fs = require('node:fs');
const path = require('node:path');
const validateCaseBundleManifest = require('./generated/case-bundle-v1-validator.cjs');

const AGENT_INSTRUCTION_FILES = new Set(['AGENTS.md', 'AGENTS.override.md']);

function assertRelativePath(value, field) {
  const normalized = value.replace(/\\/g, '/');
  if (path.isAbsolute(value) || normalized === '..' || normalized.startsWith('../') || normalized.includes('/../')) {
    throw new Error(`${field} escapes the CaseBundle`);
  }
  return normalized;
}

function inspectTree(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (AGENT_INSTRUCTION_FILES.has(entry.name)) {
      throw new Error(`Agent instruction files are not allowed in a CaseBundle: ${entry.name}`);
    }
    if (entry.name === '.git') throw new Error('.git directories are not allowed in a CaseBundle');
    const target = path.join(directory, entry.name);
    const stat = fs.lstatSync(target);
    if (stat.isSymbolicLink()) throw new Error(`symbolic link is not allowed in a CaseBundle: ${entry.name}`);
    if (stat.isDirectory()) inspectTree(target);
  }
}

function validateAcceptancePaths(check, field) {
  for (const key of ['path', 'source', 'digest']) {
    if (check[key] !== undefined) assertRelativePath(check[key], `${field}.${key}`);
  }
  if (check.paths !== undefined) {
    check.paths.forEach((value, index) => assertRelativePath(value, `${field}.paths[${index}]`));
  }
}

function variantLabel(instancePath) {
  if (instancePath.startsWith('/variants/bad')) return 'Bad Case';
  if (instancePath.startsWith('/variants/good')) return 'Good Case';
  return 'CaseBundle';
}

function schemaFailure(manifest) {
  const errors = validateCaseBundleManifest.errors || [];
  const missingVariant = errors.find((error) => error.keyword === 'required'
    && error.instancePath === '/variants'
    && ['bad', 'good'].includes(error.params.missingProperty));
  if (missingVariant) {
    const label = missingVariant.params.missingProperty === 'bad' ? 'Bad Case' : 'Good Case';
    return new Error(`CaseBundle requires a ${label}`);
  }
  if (errors.some((error) => error.instancePath.startsWith('/privacyReview'))) {
    return new Error('CaseBundle privacy review must be confirmed');
  }
  if (errors.some((error) => error.instancePath.startsWith('/provenance/sanitized'))) {
    return new Error('CaseBundle provenance must confirm sanitized input');
  }
  const unsupportedAcceptance = errors.find((error) => error.keyword === 'enum'
    && /\/acceptance\/\d+\/type$/.test(error.instancePath));
  if (unsupportedAcceptance) {
    const segments = unsupportedAcceptance.instancePath.split('/');
    const kind = segments[2];
    const index = Number(segments[4]);
    const actual = manifest.variants[kind].acceptance[index].type;
    const label = kind === 'bad' ? 'Bad Case' : 'Good Case';
    return new Error(`${label}.acceptance[${index}] has unsupported acceptance type: ${actual}`);
  }
  const error = errors[0];
  const location = error && error.instancePath ? error.instancePath : '/';
  const label = error ? variantLabel(error.instancePath) : 'CaseBundle';
  return new Error(`${label} schema invalid at ${location}: ${error ? error.message : 'unknown validation error'}`);
}

function validateVariant(bundleDirectory, familyId, kind, variant) {
  const label = kind === 'bad' ? 'Bad Case' : 'Good Case';
  if (variant.id !== `${familyId}-${kind}`) throw new Error(`${label} id must be ${familyId}-${kind}`);
  const fixture = assertRelativePath(variant.fixture, `${label} fixture`);
  const fixtureDirectory = path.resolve(bundleDirectory, fixture);
  if (!fixtureDirectory.startsWith(`${path.resolve(bundleDirectory)}${path.sep}`)
      || !fs.existsSync(fixtureDirectory) || !fs.statSync(fixtureDirectory).isDirectory()) {
    throw new Error(`${label} fixture is not a contained directory`);
  }
  variant.acceptance.forEach((check, index) => validateAcceptancePaths(check, `${label}.acceptance[${index}]`));
  return {
    id: variant.id,
    family: familyId,
    kind,
    title: variant.title,
    contract: variant.contract,
    task: variant.task,
    fixture,
    fixtureDirectory,
    acceptance: variant.acceptance
  };
}

function validateCaseBundle(directory) {
  const bundleDirectory = path.resolve(directory);
  const manifestPath = path.join(bundleDirectory, 'case.json');
  if (!fs.existsSync(manifestPath)) throw new Error(`CaseBundle is missing case.json: ${bundleDirectory}`);
  inspectTree(bundleDirectory);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (!validateCaseBundleManifest(manifest)) throw schemaFailure(manifest);
  const variants = manifest.variants;
  return {
    schemaVersion: 1,
    id: manifest.id,
    title: manifest.title,
    provenance: manifest.provenance,
    privacyReview: manifest.privacyReview,
    directory: bundleDirectory,
    cases: [
      validateVariant(bundleDirectory, manifest.id, 'bad', variants.bad),
      validateVariant(bundleDirectory, manifest.id, 'good', variants.good)
    ]
  };
}

function defaultCaseDirectories(root) {
  const casesRoot = path.join(root, 'evals', 'codex-paired', 'cases');
  return fs.readdirSync(casesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(casesRoot, entry.name));
}

function loadCaseBundles(root = path.resolve(__dirname, '..'), caseDirectories = []) {
  const directories = caseDirectories.length > 0 ? caseDirectories : defaultCaseDirectories(root);
  const bundles = directories.map(validateCaseBundle).sort((left, right) => left.id.localeCompare(right.id));
  const ids = new Set();
  for (const bundle of bundles) {
    if (ids.has(bundle.id)) throw new Error(`duplicate CaseBundle id: ${bundle.id}`);
    ids.add(bundle.id);
  }
  return bundles;
}

module.exports = { loadCaseBundles, validateCaseBundle };
