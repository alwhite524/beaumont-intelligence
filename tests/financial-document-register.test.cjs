const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');

const register = JSON.parse(fs.readFileSync('data/financial-document-register.json', 'utf8'));
assert.equal(register.documents.length, 10);
assert.equal(register.documents.filter(document => document.type === 'audit').length, 6);
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
assert.match(librarySource, /Annual Comprehensive Financial Report for the Year Ended June 30, 2024/);
assert.match(librarySource, /Annual Comprehensive Financial Report for the Year Ended June 30, 2025/);
assert.match(librarySource, /City of Beaumont FY2024 Budget Book/);

const archivePage = fs.readFileSync('docs/budgets-audits.html', 'utf8');
const viewerLinks = [...archivePage.matchAll(/href="(documents\/viewer\.html\?[^\"]+)"/g)]
  .map(match => new URL(match[1].replaceAll('&amp;', '&'), 'https://beaumontintelligence.com/'));
for (const document of register.documents) {
  const publicPath = document.localPath.replace(/^docs\//, '');
  assert.ok(viewerLinks.some(link => link.searchParams.get('url') === `../${publicPath}`), `Archive page does not open ${publicPath} in the viewer`);
}

const homePage = fs.readFileSync('docs/index.html', 'utf8');
const centersPage = fs.readFileSync('docs/intelligence-centers.html', 'utf8');
const budgetCenter = fs.readFileSync('docs/budget.html', 'utf8');
assert.match(homePage, /href="intelligence-centers\.html"/);
assert.match(centersPage, /href="budget\.html"/);
assert.match(budgetCenter, /href="budgets-audits\.html"/);

console.log('Financial document register, archive page, and ten preserved PDFs passed.');
