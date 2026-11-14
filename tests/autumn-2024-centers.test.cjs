const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const read = p => fs.readFileSync(p, 'utf8');
const data = JSON.parse(read('data/council/2024-autumn-center-review.json'));
const page = 'docs/autumn-2024-center-review.html';
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
      assert.ok(read(`docs/briefings/${day}-sources.html`).includes(`../autumn-2024-center-review.html#${r.id}`));
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

test('center blocks and the canonical review have working local anchors and viewer source routes', () => {
  const targets = new Set([page, 'docs/intelligence-centers.html', 'docs/council-intelligence.html', ...data.dates.map(d => `docs/briefings/${d}-sources.html`), ...data.findings.flatMap(r => r.pages.map(p => 'docs/' + p))]);
  const canonical = read(page);
  const ids = [...canonical.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(new Set(ids).size, ids.length);
  for (const r of data.findings) assert.ok(ids.includes(r.id));
  const manifest = JSON.parse(read('data/document-storage-manifest.json')).documents;
  for (const file of targets) {
    const html = read(file);
    const block = file === page ? html : html.match(/<!-- autumn-2024-center-review:start -->([\s\S]*?)<!-- autumn-2024-center-review:end -->/)?.[1];
    assert.ok(block, file);
    for (const [,raw] of block.matchAll(/href="([^"]+)"/g)) {
      const url = new URL(raw.replaceAll('&amp;', '&'), 'https://test.local/' + file.slice(5));
      if (url.origin !== 'https://test.local') continue;
      const target = 'docs' + decodeURIComponent(url.pathname);
      assert.ok(fs.existsSync(target), `${file}: ${raw}`);
      if (url.hash) assert.ok(read(target).includes(`id="${decodeURIComponent(url.hash.slice(1))}"`), `${file}: ${raw}`);
      if (url.pathname.endsWith('/documents/viewer.html')) {
        const source = url.searchParams.get('url');
        assert.ok(manifest.some(d => d.url === source && d.sha256), source);
      }
    }
  }
});

test('all findings are discoverable in site search and Research Library', () => {
  const search = {window: {}};
  vm.runInNewContext(read('docs/search-index.js'), search);
  const library = {window: {}};
  vm.runInNewContext(read('docs/documents/library-index.js'), library);
  for (const r of data.findings) {
    assert.equal(search.window.BI_SEARCH_INDEX.filter(x => x.url === `autumn-2024-center-review.html#${r.id}`).length, 1);
    assert.equal(library.window.BI_RESEARCH_LIBRARY.filter(x => x.url === `../autumn-2024-center-review.html#${r.id}`).length, 1);
  }
  assert.match(read('scripts/build_all.py'), /"build_service_area_actions.py",\s*"build_autumn_2024_center_updates.py"/);
});

test('new card layout is scoped and linked correctly from nested pages', () => {
  assert.match(read('docs/autumn-2024-centers.css'), /\.story-grid\.archive-review-grid/);
  for (const file of ['docs/pennsylvania-grade-separation.html', page]) {
    assert.match(read(file), /href="autumn-2024-centers.css\?v=20261113"/);
    assert.match(read(file), /story-grid archive-review-grid/);
  }
  for (const file of ['docs/dossiers/billboards.html', 'docs/briefings/2024-12-17-sources.html']) {
    assert.match(read(file), /href="\.\.\/autumn-2024-centers.css\?v=20261113"/);
  }
});
