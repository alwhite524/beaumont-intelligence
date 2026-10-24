const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const read = path => fs.readFileSync(path, 'utf8');
const review = JSON.parse(read('data/council/2026-autumn-minutes-review.json'));

test('both unchanged Word originals are registered and archived with matching checksums', () => {
  const intake = JSON.parse(read('data/council/2026-autumn-minutes-intake.json'));
  const register = JSON.parse(read('data/council/minutes-register.json')).documents;
  const manifest = JSON.parse(read('data/document-storage-manifest.json')).documents;
  for (const file of intake.documents) {
    const minute = register.find(row => row.archivePath === file.archivePath);
    const archive = manifest.find(row => row.path === file.archivePath);
    assert.equal(minute.sha256, file.sha256);
    assert.equal(archive.sha256, file.sha256);
    assert.ok(archive.bytes > 0);
    assert.match(minute.title, /Word original/);
    assert.ok(minute.textPages[0].includes('CITY COUNCIL CLOSED & REGULAR SESSION'));
    assert.ok(!minute.textPages[0].includes('October 20, 2026\nClosed Session'));
  }
});

test('September 15 preserves the missing G.16 vote and G.1 date discrepancies', () => {
  const meeting = review.meetings['2026-09-15'];
  const g16 = meeting.items.find(row => row.item === 'G.16');
  assert.equal(g16.vote, 'Not stated in supplied minutes');
  const page = read('docs/briefings/2026-09-15.html');
  assert.equal((page.match(/id="minutes-review"/g) || []).length, 1);
  assert.match(page, /August 18 minutes/);
  assert.match(page, /September 1 minutes/);
  assert.match(page, /transcript records 5–0 adoption, while the supplied minutes omit/);
  assert.equal(meeting.items.filter(row => /^J\./.test(row.item) && row.vote === 'Unanimous').length, 6);
});

test('October 6 distinguishes consensus, 4–0 approvals and the final Trevino funding motion', () => {
  const meeting = review.meetings['2026-10-06'];
  assert.match(meeting.attendance, /Martinez was absent/);
  assert.equal(meeting.items.find(row => row.item === 'J.1').vote, 'Consensus; no roll-call total stated');
  const skate = meeting.items.find(row => row.item === 'J.5');
  assert.equal(skate.vote, '4–0');
  assert.match(skate.summary, /competitively|competitive bidding/);
  assert.match(skate.summary, /budget adjustment/);
  assert.match(skate.limit, /not a direct award/);
  assert.equal(67462.16 + 5147.82 + 47390.02, 120000);
  const page = read('docs/briefings/2026-10-06.html');
  assert.equal((page.match(/id="minutes-review"/g) || []).length, 1);
  assert.ok(!page.includes('Outcome review in progress'));
  assert.match(page, /\$1,021,580.23/);
});

test('Word sources are direct links in the catalog and Research Library', () => {
  const context = { window: {} };
  vm.runInNewContext(read('docs/council-meeting-sources.js'), context);
  vm.runInNewContext(read('docs/documents/library-index.js'), context);
  for (const [date, meeting] of Object.entries(review.meetings)) {
    const source = context.window.BI_COUNCIL_MEETING_SOURCES.find(row => row.date === date);
    assert.ok(source.documents.some(row => row.url === meeting.minutesUrl && row.title.includes('Word original')));
    assert.ok(context.window.BI_RESEARCH_LIBRARY.some(row => row.type === 'Meeting minutes' && row.date === date && row.url === meeting.minutesUrl));
    assert.ok(read('docs/briefings/' + date + '-sources.html').includes(date + '.html#minutes-review'));
  }
});
