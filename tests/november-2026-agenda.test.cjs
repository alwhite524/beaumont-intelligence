const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const read=p=>fs.readFileSync(p,'utf8');
const agenda=JSON.parse(read('data/council/2026-11-17-agenda.json'));

test('November packet retains every contiguous bookmarked page and voting item',()=>{
  assert.equal(agenda.packetPages,1786);
  assert.equal(agenda.items.length,22);
  assert.equal(agenda.documents.length,87);
  assert.equal(new Set(agenda.documents.map(d=>d.archiveUrl)).size,87);
  let next=6;
  for(const d of agenda.documents){assert.equal(d.packet_page_start,next);assert.ok(d.packet_page_end>=next);next=d.packet_page_end+1;}
  assert.equal(next,1787);
  assert.equal(new Set(agenda.documents.map(d=>d.item)).size,22);
  assert.equal(agenda.audit.officialHtmlAuditComplete,false);
  assert.equal(agenda.nextMeeting.date,'2026-12-15');
});

test('every published source has a verified archive record and appears in the Research Library',()=>{
  const manifest=JSON.parse(read('data/document-storage-manifest.json'));
  const context=vm.createContext({window:{}});
  vm.runInContext(read('docs/documents/library-index.js'),context);
  assert.equal(agenda.audit.archiveComplete,true);
  for(const url of [agenda.packetArchiveUrl,agenda.agendaArchiveUrl,...agenda.documents.map(d=>d.archiveUrl)]){
    const r=manifest.documents.find(d=>d.url===url);assert.ok(r,url);assert.match(r.sha256,/^[a-f0-9]{64}$/);assert.ok(r.bytes>0);
    assert.ok(context.window.BI_RESEARCH_LIBRARY.some(d=>d.url===url),url);
  }
});

test('briefing separates proposals, reported amounts and attachment findings',()=>{
  const p=read('docs/briefings/2026-11-17.html');
  assert.match(p,/Closed session 5:00 PM · Regular meeting 6:00 PM/);
  assert.match(p,/\$40,512/);
  assert.match(p,/not a construction contract award/);
  assert.match(p,/Do not present March 2027 as a confirmed completion date/);
  assert.match(p,/\$1,643,493/);
  assert.match(p,/Packet p\. 491/);
});

test('home and Council routes lead to the new briefing and interactive agenda',()=>{
  for(const file of ['docs/index.html','docs/council-intelligence.html','docs/council-briefings-2026.html']){
    const p=read(file);assert.match(p,/briefings\/2026-11-17-sources\.html/);assert.doesNotMatch(p,/View (?:November 17|meeting) placeholder/);
  }
  assert.match(read('scripts/build_october_2026_update.py'),/publish_november_agenda\(\)/);
});

test('interactive agenda filters all 87 sources and opens documents inside its dialog',()=>{
  const elements={};
  function el(){return {value:'',events:{},addEventListener(n,f){this.events[n]=f;},showModal(){this.open=true;},close(){this.open=false;}};}
  for(const id of ['source-search','source-section','source-results','source-count','viewer-dialog','viewer-frame','viewer-title','viewer-close','view-packet'])elements['#'+id]=el();
  elements['#source-section'].value='all';
  const context=vm.createContext({window:{},document:{querySelector:id=>elements[id]},location:{href:'https://beaumontintelligence.com/briefings/2026-11-17-sources.html'},URL,encodeURIComponent});
  vm.runInContext(read('docs/briefings/2026-11-17-sources.js'),context);
  const page=read('docs/briefings/2026-11-17-sources.html');
  for(const m of page.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(m[1],context);
  assert.match(elements['#source-count'].textContent,/87 of 87/);
  assert.ok(elements['#source-results'].innerHTML.indexOf('Action calendar')<elements['#source-results'].innerHTML.indexOf('Consent calendar'));
  elements['#source-section'].value='Action';elements['#source-section'].events.change();assert.match(elements['#source-count'].textContent,/26 of 87/);
  elements['#source-search'].value='Axon';elements['#source-section'].value='all';elements['#source-search'].events.input();assert.match(elements['#source-results'].innerHTML,/G\.10/);
  elements['#source-results'].events.click({target:{closest:()=>({dataset:{url:agenda.documents[0].archiveUrl,title:'Source'}})}});
  assert.equal(elements['#viewer-dialog'].open,true);assert.match(elements['#viewer-frame'].src,/documents\/viewer\.html\?url=/);
  elements['#viewer-close'].events.click();assert.equal(elements['#viewer-frame'].src,'about:blank');
  elements['#view-packet'].events.click();assert.match(elements['#viewer-frame'].src,/2026-11-17-city-council-agenda-package/);
});
