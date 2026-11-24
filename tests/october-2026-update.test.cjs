const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const read = path => fs.readFileSync(path, 'utf8');
const outcomes = JSON.parse(read('data/council/2026-10-20-outcomes.json'));

test('next-meeting cards use the official November 17 date, not the canceled November 3 date', () => {
  const home = read('docs/index.html');
  const council = read('docs/council-intelligence.html');
  assert.match(home, /data-next-regular-date="2026-11-17"/);
  assert.match(home, /briefings\/2026-11-17\.html/);
  assert.match(council, /Upcoming meeting · Agenda available/);
  const november = read('docs/briefings/2026-11-17.html');
  assert.match(november, /Closed session 5:00 PM/);
  assert.match(november, /2026-11-17-sources\.html/);
  assert.doesNotMatch(november, /This is a placeholder/);
  assert.equal(outcomes.nextMeeting.date, '2026-11-17');
});

test('October outcomes preserve proposals and distinguish first readings and conditional spending', () => {
  const page = read('docs/briefings/2026-10-20.html');
  assert.equal((page.match(/id="meeting-outcomes"/g) || []).length, 1);
  assert.equal((page.match(/Preserved pre-meeting briefing and document checks/g) || []).length, 1);
  assert.match(page, /Fine schedule differs between report and ordinance/);
  assert.match(page, /Council introduced the ordinance at first reading/);
  assert.match(page, /\$241,727/);
  assert.match(page, /The transcript roll call records four yes votes and Lara voting no/);
  assert.match(page, /Decisions checked against the supplied minutes/);
  assert.match(page, /six-cent correction/);
  assert.match(page, /Dais handout verification/);
  assert.ok(fs.existsSync('docs/' + outcomes.minutes.url));
  assert.equal(JSON.parse(read('data/council/2026-10-20-agenda.json')).meetingStatus, 'held');
  for (const item of outcomes.items) {
    assert.ok(item.videoSeconds >= 0 && item.videoSeconds < outcomes.durationSeconds);
    assert.ok(page.includes(`id="outcome-${item.item}"`));
  }
});

test('October 20 minutes raise five action scores to 80% with final instruments open', () => {
  const data = JSON.parse(read('data/service-area-actions.json'));
  const actions = data.records.filter(row => row.date === outcomes.date);
  assert.equal(actions.length, 5);
  const page = read('docs/service-area-actions.html');
  for (const action of actions) {
    assert.equal(action.checks.minutes, true);
    assert.equal(action.checks.instruments, false);
    assert.match(action.evidence, /verified the corrected dais handouts/);
    assert.equal(Object.values(action.checks).filter(Boolean).length, 4);
    assert.equal(action.minutesUrl, outcomes.minutes.url);
    for (const area of action.areas) {
      const card = page.split(`id="${area}-${action.id}"`)[1].split('</article>')[0];
      assert.match(card, /Research completion: 80% · 4\/5 checks/);
    }
  }
});

test('complete caption track and its reader are available in both source catalogs', () => {
  const text = read('docs/transcripts/2026-10-20-city-council-transcript.txt');
  assert.match(text, /Source: https:\/\/www.youtube.com\/watch\?v=UVsGQHIcdkA/);
  assert.match(text, /automatically generated/);
  assert.ok(text.split('\n').filter(line => /^\(\d{2}:\d{2}:\d{2}\)/.test(line)).length > 3400);
  assert.match(text, /\(03:30:/);
  const context = { window: {} };
  vm.runInNewContext(read('docs/council-meeting-sources.js'), context);
  const meeting = context.window.BI_COUNCIL_MEETING_SOURCES.find(row => row.date === '2026-10-20');
  assert.equal(meeting.transcript, 'transcripts/reader.html?date=2026-10-20');
  assert.match(meeting.video, /UVsGQHIcdkA/);
  assert.ok(meeting.documents.some(document => document.url === outcomes.minutes.url));
  vm.runInNewContext(read('docs/documents/library-index.js'), context);
  assert.ok(context.window.BI_RESEARCH_LIBRARY.some(row => row.type === 'Meeting minutes' && row.url === '../' + outcomes.minutes.url));
  assert.ok(context.window.BI_RESEARCH_LIBRARY.some(row => row.date === '2026-10-20' && row.type === 'Meeting transcript' && row.url.includes('reader.html')));
});

test('new center findings link to evidence without inventing October 20 minutes', () => {
  const findings = JSON.parse(read('data/council/recent-center-findings.json')).records.filter(row => row.date === '2026-10-20');
  for (const finding of findings) {
    const page = read('docs/' + finding.page);
    assert.ok(page.includes(`id="${finding.id}"`), finding.page);
    assert.ok(page.includes(finding.meetingRecordUrl));
    assert.match(finding.limits, /approved October 20 minutes not yet collected/);
  }
  assert.equal(outcomes.serviceAreaReview.length, 7);
});

test('transcript reader renders and searches Windows line endings', async () => {
  class Element {
    constructor() { this.children = []; this.events = {}; this.value = ''; this.ownText = ''; }
    append(...children) { this.children.push(...children); }
    set textContent(value) { this.ownText = value; }
    get textContent() { return this.ownText + this.children.map(child => child.textContent).join(''); }
    addEventListener(name, callback) { this.events[name] = callback; }
  }
  const elements = {};
  const document = {
    querySelector: key => elements[key] ||= new Element(),
    createElement: () => new Element(),
  };
  const text = 'Source: https://www.youtube.com/watch?v=UVsGQHIcdkA\r\n\r\n(01:50:36) Police station discussion\r\n(02:43:30) Downtown design\r\n';
  await vm.runInNewContext(read('docs/transcripts/reader.js'), {
    URLSearchParams, location: { search: '?date=2026-10-20' }, document,
    fetch: async () => ({ ok: true, text: async () => text }),
  });
  const rows = elements['#transcript-lines'].children;
  assert.equal(rows.length, 2);
  assert.match(rows[0].children[0].href, /&t=6636s$/);
  elements['#transcript-search'].value = 'police';
  elements['#transcript-search'].events.input();
  assert.equal(rows[0].hidden, false);
  assert.equal(rows[1].hidden, true);
});
