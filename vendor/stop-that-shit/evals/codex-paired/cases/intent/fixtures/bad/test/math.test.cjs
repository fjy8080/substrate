'use strict';

const assert = require('node:assert/strict');
const { add } = require('../src/math.cjs');

assert.equal(add(2, 3), 5);
