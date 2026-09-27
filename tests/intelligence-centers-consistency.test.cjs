const assert = require('node:assert/strict');
const fs = require('node:fs');

const centerPages = [
  'potrero-interchange.html',
  'pennsylvania-grade-separation.html',
  'police.html',
  'animal-control.html',
  'downtown-revitalization.html',
  'stewart-park.html',
  'budget.html',
  'wrcog-restitution.html',
  'wrcog-restitution-evidence.html',
];
const sharedStructure = ['<body data-page=', 'skip-link', 'app-header', 'breadcrumbs', 'project-nav', 'footer-grid', 'app.js'];
for (const page of centerPages) {
  const html = fs.readFileSync(`docs/${page}`, 'utf8');
  for (const marker of sharedStructure) {
    assert.ok(html.includes(marker), `${page} is missing shared Center structure: ${marker}`);
  }
}

const directory = fs.readFileSync('docs/intelligence-centers.html', 'utf8');
assert.equal((directory.match(/class="center-number"/g) || []).length, 7);
assert.equal((directory.match(/href="wrcog-restitution\.html"/g) || []).length, 1);
const financeCard = directory.match(/<article class="center-card" id="finance-government">[\s\S]*?<\/article>/)?.[0] || '';
assert.match(financeCard, /href="budget\.html"/);
assert.match(financeCard, /href="wrcog-restitution\.html"/);
assert.match(financeCard, /href="council-intelligence\.html"/);

const wrcog = fs.readFileSync('docs/wrcog-restitution.html', 'utf8');
assert.match(wrcog, /intelligence-centers\.html#finance-government/);
assert.match(wrcog, /class="project-nav center-nav"/);
assert.match(wrcog, /href="wrcog-restitution-evidence\.html">Evidence<\/a>/);
assert.match(wrcog, /class="status-layout"/);
assert.match(wrcog, /class="snapshot-card"/);
assert.ok((wrcog.match(/class="story-card"/g) || []).length >= 5);
console.log('Intelligence Center hierarchy and shared page structure passed.');
