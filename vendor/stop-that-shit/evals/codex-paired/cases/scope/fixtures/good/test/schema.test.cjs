'use strict';

const assert = require('node:assert/strict');
const record = require('../src/schema.cjs');
const { render } = require('../src/consumer.cjs');

assert.equal(record.label, 'Ada');
assert.equal(Object.hasOwn(record, 'name'), false);
assert.equal(render(record), 'Ada');
