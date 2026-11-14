const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const read=p=>fs.readFileSync(p,'utf8');
const dates=[['2024-10-01',1299,54],['2024-10-15',1523,45],['2024-11-19',619,51],['2024-12-03',270,37],['2024-12-17',1277,73]];
const load=d=>JSON.parse(read(`data/council/${d}-agenda.json`));

test('five source-audited inventories retain all 4988 pages and 260 unique document ranges',()=>{
  let pages=0,documents=0;
  for(const [date,count,total] of dates){
    const a=load(date);pages+=a.packetPages;documents+=a.documents.length;
    assert.equal(a.packetPages,count);assert.equal(a.documents.length,total);assert.equal(a.audit.expectedDocuments,total);assert.equal(a.audit.linkedDocuments,total);assert.equal(a.audit.officialHtmlAuditComplete,true);assert.match(a.audit.officialHtmlSha256,/^[a-f0-9]{64}$/);
    assert.equal(new Set(a.documents.map(d=>d.archiveUrl)).size,total);
    let next=a.agendaPageCount+1;
    for(const d of a.documents){assert.equal(d.packet_page_start,next);assert.ok(d.packet_page_end>=next);next=d.packet_page_end+1;assert.ok(a.items.some(i=>i.item===d.item&&i.section===d.section));assert.match(d.officialUrl,/^https:\/\/pub-beaumont\.escribemeetings\.com\/(?:f|F)ile[sS]tream\.ashx\?DocumentId=\d+$/);}
    assert.equal(next,count+1);
  }
  assert.equal(pages,4988);assert.equal(documents,260);
});

test('October 15 uses actual section headings instead of fixed letter assumptions',()=>{
  const a=load('2024-10-15'),byId=id=>a.items.find(i=>i.item===id);
  assert.equal(byId('B.1').section,'Presentation');
  assert.equal(byId('D.1').section,'Consent');
  assert.equal(byId('F.1').section,'Public Hearing');
  assert.equal(byId('G.1').section,'Action');
  assert.equal(byId('G.3').section,'Action');
  assert.equal(byId('J').section,'Reports');
  assert.equal(a.items.some(i=>i.section==='Closed Session'),false);
  assert.equal(a.documents.find(d=>d.item==='G.3').section,'Action');
  const page=read('docs/briefings/2024-10-15-sources.html');
  assert.ok(page.indexOf('<h2>Public Hearing</h2>')<page.indexOf('<h2>Action</h2>'));assert.ok(page.indexOf('<h2>Action</h2>')<page.indexOf('<h2>Consent</h2>'));
});

test('treasurer attachments remain attached to the unnumbered report entries',()=>{
  for(const [date,id] of [['2024-10-01','M'],['2024-10-15','J']]){
    const a=load(date),item=a.items.find(i=>i.item===id),docs=a.documents.filter(d=>d.item===id);
    assert.equal(item.section,'Reports');assert.equal(docs.length,3);
    assert.ok(docs.every(d=>d.packetBookmarkTitle.startsWith(id+'. ')));
    const page=read(`docs/briefings/${date}-sources.html`);assert.ok(page.includes(`id="item-${id.toLowerCase()}"`));
    for(const d of docs)assert.ok(page.includes(`data-document-url="${d.archiveUrl}"`));
  }
});

test('all documents and proposed recommendations appear with original-source links and viewer controls',()=>{
  for(const [date,,count] of dates){
    const a=load(date),page=read(`docs/briefings/${date}-sources.html`),context=vm.createContext({window:{}});
    vm.runInContext(read(`docs/briefings/${date}-sources.js`),context);
    assert.equal(context.window['BI_AUTUMN_'+date.replaceAll('-','_')+'_SOURCES'].length,count);
    assert.equal((page.match(/class="packet-document"/g)||[]).length,count);
    assert.equal((page.match(/data-document-url=/g)||[]).length,count+2);
    assert.match(page,/Published recommendation:/);assert.match(page,/A recommendation is not a Council decision/);
    assert.doesNotMatch(page,/\b(?:CONFIG|GROUPS|MINUTESURL|LABEL|COUNT)\b/);
    for(const d of a.documents){assert.ok(page.includes(d.archiveUrl));assert.ok(page.includes('Packet pages '+d.packet_page_start+'–'+d.packet_page_end));}
  }
});

test('all five packets and extracted PDFs have verified archive sizes and checksums',()=>{
  const manifest=JSON.parse(read('data/document-storage-manifest.json'));
  for(const [date] of dates){const a=load(date);assert.equal(a.audit.archiveComplete,true);
    for(const url of [a.packetArchiveUrl,a.agendaUrl,...a.documents.map(d=>d.archiveUrl)]){const r=manifest.documents.find(d=>d.url===url);assert.ok(r,url);assert.match(r.sha256,/^[a-f0-9]{64}$/);assert.ok(r.bytes>0);}
    assert.equal(manifest.documents.find(d=>d.url===a.packetArchiveUrl).bytes,a.packetBytes);
  }
});

test('Council overview, meeting catalog and library connect every agenda and supporting document',()=>{
  const context=vm.createContext({window:{}});vm.runInContext(read('docs/council-meeting-sources.js'),context);vm.runInContext(read('docs/documents/library-index.js'),context);
  const page=read('docs/council-intelligence.html');assert.equal((page.match(/id="autumn-2024-agendas"/g)||[]).length,1);
  for(const [date] of dates){const a=load(date),record=context.window.BI_COUNCIL_MEETING_SOURCES.find(r=>r.date===date);
    assert.equal(record.interactiveAgenda,`briefings/${date}-sources.html`);assert.equal(record.packet,a.packetArchiveUrl);assert.ok(record.minutes);assert.ok(page.includes(record.interactiveAgenda));
    for(const d of a.documents)assert.ok(context.window.BI_RESEARCH_LIBRARY.some(r=>r.url===d.archiveUrl&&r.item===d.item));
    for(const i of a.items)assert.ok(context.window.BI_RESEARCH_LIBRARY.some(r=>r.date===date&&r.type==='Agenda item'&&r.item===i.item));
  }
  assert.ok(context.window.BI_COUNCIL_MEETING_SOURCES.find(r=>r.date==='2024-10-01').video);
});
