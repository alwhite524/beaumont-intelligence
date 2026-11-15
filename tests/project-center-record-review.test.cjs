const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const crypto=require('node:crypto');
const read=p=>fs.readFileSync(p,'utf8');
const data=JSON.parse(read('data/council/2025-spring-center-review.json'));
const corpus=JSON.parse(read('data/council/project-center-inventory.json'));
const byId=id=>data.findings.find(r=>r.id==='project-review-'+id);

test('all four missing packets are screened with exact source item references',()=>{
 assert.deepEqual(data.dates,['2025-03-04','2025-03-18','2025-04-01','2025-04-15']);
 assert.equal(data.coverage.length,108);
 assert.equal(data.findings.length,34);
 for(const day of data.dates){
  const packet=JSON.parse(read(`data/council/${day}-agenda.json`));
  assert.deepEqual(data.coverage.filter(r=>r.date===day).map(r=>r.item),packet.items.map(i=>i.item));
  assert.doesNotMatch(read(`docs/briefings/${day}-sources.html`),/Project center findings from this meeting/);
 }
 for(const row of data.findings){
  const packet=JSON.parse(read(`data/council/${row.date}-agenda.json`));
  for(const item of row.items) assert.ok(packet.items.some(i=>i.item===item));
 }
 assert.equal(byId('fairway-initial-emergency').items.length,0);
 assert.deepEqual(byId('fairway-initial-emergency').minutesPages,[3,8]);
});

test('source inventory covers all dated item arrays, project timeline and collected minutes without claiming outcomes',()=>{
 assert.equal(corpus.agendaItemCount,corpus.entries.length);
 assert.equal(new Set(corpus.entries.map(r=>r.date+'|'+r.item)).size,corpus.entries.length);
 assert.ok(corpus.agendaItemCount>=708);
 assert.ok(corpus.agendaMeetingCount>=38);
 assert.equal(corpus.minutesDocumentCount,JSON.parse(read('data/council/minutes-register.json')).documents.length);
 assert.ok(corpus.inputs.some(r=>r.path==='docs/data.js'));
 for(const input of corpus.inputs){
  assert.equal(input.sha256,crypto.createHash('sha256').update(fs.readFileSync(input.path)).digest('hex'),input.path);
 }
 assert.ok(corpus.entries.some(r=>r.date==='2026-10-06'&&r.item==='J.5'));
 assert.match(corpus.scope,/not a full|not substantive/);
});

test('project funding keeps amounts, pending grants, duplicates and discrepancies distinct',()=>{
 const costs=byId('potrero-costs');
 for(const x of ['$75,819,000','$68,113,000','$7,706,000','$79,306,257','$79,252,046','$71,904,000','$78,952,046']) assert.ok(costs.summary.includes(x));
 assert.match(byId('potrero-funding').status,/omit a carried result/);
 assert.match(byId('potrero-tumf').limit,/do not establish restitution/);
 assert.match(byId('pennsylvania-grants').limit,/not funds to sum/);
 assert.match(byId('sb125-project-label').limit,/not evidence of two awards/);
 assert.match(byId('stewart-orlp').limit,/\$2.5 million/);
 assert.match(byId('stewart-orlp').summary,/\$3.1 million/);
 assert.match(byId('second-street-award').limit,/not another award/);
 assert.match(byId('cherry-channel').limit,/\$400 difference/);
});

test('recommendations do not replace votes, actual spending or future outcomes',()=>{
 assert.match(byId('crc-parking').summary,/Option 1.*Option 3/);
 assert.match(byId('crc-parking').status,/3-2/);
 assert.match(byId('event-waiver-tabled').status,/Tabled/);
 assert.match(byId('cherry-festival').summary,/\$100,000/);
 assert.match(byId('cherry-festival').limit,/\$135,000/);
 assert.match(byId('beaumont-nights').summary,/\$508,101/);
 assert.match(byId('beaumont-nights').limit,/not actual expenditure or a three-year total/);
 assert.match(byId('stewart-latest-packet').status,/Upcoming recommendation/);
 assert.match(byId('stewart-latest-packet').summary,/January 2027/);
 assert.match(byId('october-draft-minutes').limit,/do not establish approved minutes/);
 assert.match(byId('october-draft-minutes').summary,/\$241,727/);
});
