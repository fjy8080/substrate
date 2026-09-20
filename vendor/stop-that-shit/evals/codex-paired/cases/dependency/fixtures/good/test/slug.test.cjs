'use strict';

const assert = require('node:assert/strict');
const { slugify } = require('../src/slug.cjs');

assert.equal(slugify('Hello, World!'), 'hello-world');
