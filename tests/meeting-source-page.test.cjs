const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');

const catalog = fs.readFileSync('docs/council-meeting-sources.js');
const page = fs.readFileSync('docs/council-meeting-sources.html', 'utf8');
const version = crypto.createHash('sha256').update(catalog).digest('hex').slice(0, 12);
assert.ok(page.includes(`council-meeting-sources.js?v=${version}`), 'Page must request the current catalog version');

const elements = Object.fromEntries(['#meeting-source-list', '#meeting-source-count', '#minutes-compilations'].map(id => [id, {}]));
const context = vm.createContext({window: {}, document: {querySelector: id => elements[id]}, Intl});
vm.runInContext(catalog.toString(), context);
for (const script of page.matchAll(/<script>([\s\S]*?)<\/script>/g)) vm.runInContext(script[1], context);
const rows = elements['#meeting-source-list'].innerHTML.match(/<article\b[\s\S]*?<\/article>/g);
for (const date of ['2022-01-04', '2022-01-18', '2022-02-01', '2022-02-15', '2022-03-01', '2022-03-15', '2022-04-05']) {
  const row = rows.find(row => row.includes(`briefings/${date}-sources.html`));
  assert.ok(row, `${date} interactive agenda must appear`);
  assert.ok(row.includes('documents/viewer.html?url='), `${date} PDFs must use the viewer`);
  if (date !== '2022-01-04') {
    assert.ok(row.includes(`transcripts/reader.html?date=${date}`));
    assert.ok(row.includes('Full YouTube video'));
  }
}
console.log('Meeting page renders seven agendas, six transcripts, and viewer links with a current catalog version.');
