const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');

const register = JSON.parse(fs.readFileSync('data/financial-document-register.json', 'utf8'));
assert.equal(register.documents.length, 8);
assert.equal(register.documents.filter(document => document.type === 'audit').length, 4);
assert.equal(register.documents.filter(document => document.type === 'budget').length, 4);

for (const document of register.documents) {
  assert.ok(fs.existsSync(document.localPath), `Missing ${document.localPath}`);
  const bytes = fs.readFileSync(document.localPath);
  assert.equal(bytes.subarray(0, 5).toString('ascii'), '%PDF-', `${document.localPath} is not a PDF`);
  assert.equal(bytes.length, document.bytes, `${document.localPath} size changed`);
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex').toUpperCase(), document.sha256,
    `${document.localPath} checksum changed`);
}

const librarySource = fs.readFileSync('docs/documents/library-index.js', 'utf8');
assert.match(librarySource, /Annual Comprehensive Financial Report for the Year Ended June 30, 2022/);
assert.match(librarySource, /City of Beaumont FY2024 Budget Book/);

console.log('Financial document register and eight preserved PDFs passed.');
