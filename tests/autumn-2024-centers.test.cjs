const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const read = p => fs.readFileSync(p, 'utf8');
const data = JSON.parse(read('data/council/2024-autumn-center-review.json'));
const byId = id => data.findings.find(r => r.id === 'autumn-2024-' + id);

test('review accounts for all 98 agenda entries and references real source items', () => {
  assert.equal(data.coverage.length, 98);
  assert.equal(data.findings.length, 35);
  assert.equal(new Set(data.findings.map(r => r.id)).size, 35);
  for (const day of data.dates) {
    const packet = JSON.parse(read(`data/council/${day}-agenda.json`));
    const coverage = data.coverage.filter(r => r.date === day);
    assert.deepEqual(coverage.map(r => r.item), packet.items.map(r => r.item));
    for (const r of data.findings.filter(r => r.date === day)) {
      assert.ok(r.minutesPages.length && r.minutesPages.every(p => p > 0));
      for (const item of r.items) assert.ok(packet.items.some(i => i.item === item));
      assert.doesNotMatch(read(`docs/briefings/${day}-sources.html`), /autumn-2024-center-review\.html/);
      for (const p of r.pages) assert.ok(fs.existsSync('docs/' + p));
    }
  }
});

test('continuances, report receipt, missing tallies and applications retain their limits', () => {
  assert.match(byId('dif-continuance').status, /Continued 4-1/);
  assert.match(byId('dif-continuance').summary, /not adopted/);
  assert.match(byId('potrero-benefit').status, /receive and file/);
  assert.match(byId('potrero-benefit').limit, /did not approve/);
  assert.match(byId('plot-plan-withdrawn').status, /Removed/);
  for (const id of ['financial-policies', 'cdbg-supplement', 'fy2024-audit', 'budget-timeline']) {
    const row = byId(id);
    assert.match(row.limit, /omit|omits/);
    assert.doesNotMatch(row.status, /Approved unanimously/);
  }
  assert.match(byId('cdbg-applications').limit, /not final grant awards/);
});

test('Pennsylvania and funding changes distinguish balances, new authority and unresolved amounts', () => {
  const design = byId('pennsylvania-design');
  for (const amount of ['$1,884,482', '$1,209,191', '$675,291', '$3,134,124']) assert.ok(design.summary.includes(amount));
  assert.match(design.limit, /September 2025/);
  const environmental = byId('pennsylvania-environment');
  assert.ok(environmental.summary.includes('$86,698') && environmental.summary.includes('$86,989'));
  assert.match(environmental.limit, /\$291 difference remains unresolved/);
  assert.match(byId('pennsylvania-sb125').summary, /\$13,678,556/);
  assert.match(byId('second-street-grant').limit, /same \$1 million.*not an additional grant/);
  assert.match(byId('tumf-update').limit, /not evidence of a settlement payoff/);
});

test('agenda batch reviews stay out of public navigation and indexes', () => {
  const reviews = /autumn-2024-center-review|project-center-record-review/;
  for (const page of ['budget-records', 'council-intelligence', 'intelligence-centers', 'land-policy']) {
    assert.doesNotMatch(read('docs/' + page + '.html'), reviews);
  }
  for (const [file, global] of [['search-index.js', 'BI_SEARCH_INDEX'], ['documents/library-index.js', 'BI_RESEARCH_LIBRARY']]) {
    const context = {window: {}};
    vm.runInNewContext(read('docs/' + file), context);
    assert.ok(context.window[global].every(row => !reviews.test(row.url)));
  }
});
