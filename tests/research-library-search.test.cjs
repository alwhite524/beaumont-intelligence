const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const control = value => ({
  value,
  hidden: false,
  listeners: {},
  addEventListener(name, callback) { this.listeners[name] = callback; },
});

const search = control('');
const topic = control('all');
const meeting = control('all');
meeting.innerHTML = '';
const count = { textContent: '' };
const empty = { hidden: false };
const rows = Array.from({ length: 3 }, () => ({ hidden: false }));
const groups = Array.from({ length: 2 }, () => ({ hidden: false }));
const topics = {
  hidden: false,
  querySelectorAll(selector) { return selector === '.record' ? rows : groups; },
  before(element) { this.results = element; },
};
const statuses = [{ textContent: '' }, { textContent: '' }];
const modes = ['documents', 'transcripts', 'minutes'].map(value => ({ ...control(value), checked: value === 'documents' }));
const document = {
  querySelector(selector) {
    return ({ '#search': search, '#topic': topic, '#meeting': meeting,
      '#topics': topics, '#count': count, '#empty': empty })[selector] || null;
  },
  querySelectorAll(selector) {
    return selector === '.library-hero .status span' ? statuses : selector === 'input[name="search-mode"]' ? modes : [];
  },
  createElement() { return { className: '', hidden: false, innerHTML: '' }; },
  addEventListener() {},
};
const records = [
  { title: 'Billboard staff report', url: 'https://documents.beaumontintelligence.com/billboard.pdf', date: '2026-09-01', item: 'J.1', topic: 'transportation', type: 'Archived document', body: 'Digital billboard agreement' },
  { title: 'Park plan', url: 'https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId=1', date: '2026-08-18', item: 'G.2', topic: 'parks', type: 'Official City document', body: 'Park plan' },
  { title: '2018 transcript', url: '../transcripts/2018.txt', videoUrl: 'https://www.youtube.com/watch?v=abc', date: '2018-06-19', item: '', topic: 'council', type: 'Meeting transcript', body: '(5:25:07) Council discussed digital billboards.' },
];
records.push({ title: '2020 Council minutes', url: 'https://documents.beaumontintelligence.com/minutes.pdf', date: '2020-11-03', topic: 'council', type: 'Meeting minutes', body: 'WRCOG lawsuit authorization' });
const context = vm.createContext({ window: { BI_RESEARCH_LIBRARY: records }, document, URL, console });
vm.runInContext(fs.readFileSync('docs/documents/library-search.js', 'utf8'), context);

assert.match(meeting.innerHTML, /2026-09-01/);
assert.match(meeting.innerHTML, /2026-08-18/);
assert.doesNotMatch(meeting.innerHTML, /2018-06-19/);
assert.match(count.textContent, /3 source collections/);

search.value = 'bill board';
search.listeners.input();
assert.match(topics.results.innerHTML, /View document/);
assert.match(topics.results.innerHTML, /viewer\.html\?url=/);
assert.doesNotMatch(topics.results.innerHTML, /Watch video/);
modes[0].checked = false; modes[1].checked = true;
modes[1].listeners.change();
assert.match(topics.results.innerHTML, /Watch video at 5:25:07/);
assert.match(topics.results.innerHTML, /t=19507s/);
assert.match(count.textContent, /1 matching meeting transcript/);
modes[1].checked = false; modes[0].checked = true; modes[0].listeners.change();

search.value = '';
topic.value = 'transportation';
topic.listeners.change();
assert.match(count.textContent, /Showing 1 source document/);
assert.doesNotMatch(topics.results.innerHTML, /Meeting transcript/);

topic.value = 'all';
meeting.value = '2026-08-18';
meeting.listeners.change();
assert.match(count.textContent, /Showing 1 source document/);
assert.match(topics.results.innerHTML, /Park plan/);

modes[0].checked = false; modes[2].checked = true; meeting.value = 'all'; search.value = 'WRCOG';
modes[2].listeners.change();
assert.equal(topic.disabled, true);
assert.match(meeting.innerHTML, /2020-11-03/);
assert.doesNotMatch(meeting.innerHTML, /2018-06-19/);
assert.match(topics.results.innerHTML, /2020 Council minutes/);
assert.match(topics.results.innerHTML, /viewer.html/);
assert.doesNotMatch(topics.results.innerHTML, /Billboard staff report/);
search.value = 'absent phrase'; search.listeners.input();
assert.match(topics.results.innerHTML, /No minutes/);
console.log('Research Library documents, transcripts and minutes behavior passed.');
