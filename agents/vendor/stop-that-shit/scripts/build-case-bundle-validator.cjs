#!/usr/bin/env node

'use strict';

const fs = require('node:fs');
const path = require('node:path');
const Ajv2020 = require('ajv/dist/2020');
const standaloneCode = require('ajv/dist/standalone');

const root = path.resolve(__dirname, '..');
const schemaPath = path.join(root, 'schemas', 'case-bundle-v1.schema.json');
const outputPath = path.join(__dirname, 'generated', 'case-bundle-v1-validator.cjs');

function generateValidatorSource() {
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  const ajv = new Ajv2020({
    allErrors: true,
    strict: true,
    strictRequired: false,
    code: { source: true }
  });
  const validate = ajv.compile(schema);
  return `${standaloneCode(ajv, validate)}\n`;
}

function main() {
  const generated = generateValidatorSource();
  if (process.argv.includes('--check')) {
    const current = fs.existsSync(outputPath) ? fs.readFileSync(outputPath, 'utf8') : '';
    if (current.replace(/\r\n/g, '\n') !== generated.replace(/\r\n/g, '\n')) {
      process.stderr.write('CaseBundle validator is stale; run npm run schema:build\n');
      process.exitCode = 1;
      return;
    }
    process.stdout.write('PASS generated CaseBundle validator is current\n');
    return;
  }
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, generated, 'utf8');
  process.stdout.write(`${outputPath}\n`);
}

if (require.main === module) main();

module.exports = { generateValidatorSource, outputPath };
