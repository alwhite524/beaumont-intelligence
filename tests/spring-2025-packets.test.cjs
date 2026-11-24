const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const read=p=>fs.readFileSync(p,'utf8');
const dates=[['2025-03-04',1595,99],['2025-03-18',789,68],['2025-04-01',137,26],['2025-04-15',475,72]];
const load=d=>JSON.parse(read(`data/council/${d}-agenda.json`));

test('four packet inventories preserve all 265 matched attachments and every packet page',()=>{
  let total=0;
  for(const [day,pages,docs] of dates){
    const a=load(day);assert.equal(a.packetPages,pages);assert.equal(a.documents.length,docs);total+=docs;
    assert.equal(a.audit.expectedDocuments,docs);assert.equal(a.audit.linkedDocuments,docs);assert.equal(a.audit.officialHtmlAuditComplete,true);assert.match(a.audit.officialHtmlSha256,/^[a-f0-9]{64}$/);
    assert.equal(new Set(a.documents.map(d=>d.archiveUrl)).size,docs);
    let next=a.agendaPageCount+1;
    for(const d of a.documents){assert.equal(d.packet_page_start,next);assert.ok(d.packet_page_end>=next);next=d.packet_page_end+1;assert.ok(a.items.some(i=>i.item===d.item));assert.match(d.officialUrl,/^https:\/\/pub-beaumont\.escribemeetings\.com\/(?:f|F)ile[sS]tream\.ashx\?DocumentId=\d+$/);}
    assert.equal(next,pages+1);
    const context=vm.createContext({window:{}});vm.runInContext(read(`docs/briefings/${day}-sources.js`),context);
    assert.equal(context.window['BI_SPRING_'+day.replaceAll('-','_')+'_SOURCES'].length,docs);
  }
  assert.equal(total,265);
});

test('all four packets, agenda extracts and attachments have verified archive objects',()=>{
  const manifest=JSON.parse(read('data/document-storage-manifest.json'));
  for(const [date] of dates){const a=load(date);assert.equal(a.audit.archiveComplete,true);
    for(const url of [a.packetArchiveUrl,a.agendaUrl,...a.documents.map(d=>d.archiveUrl)]){const object=manifest.documents.find(r=>r.url===url);assert.ok(object,url);assert.match(object.sha256,/^[a-f0-9]{64}$/);assert.ok(object.bytes>0);}
    assert.equal(manifest.documents.find(r=>r.url===a.packetArchiveUrl).bytes,a.packetBytes);
  }
});

test('all supporting documents render in the agenda and original City links remain available',()=>{
  for(const [date,,count] of dates){const a=load(date),page=read(`docs/briefings/${date}-sources.html`);
    assert.match(page,/Published recommendation:/);assert.match(page,/Original City source/);
    assert.equal((page.match(/class="packet-document"/g)||[]).length,count);
    for(const d of a.documents){assert.ok(page.includes(`data-document-url="${d.archiveUrl}"`));assert.ok(page.includes('Packet pages '+d.packet_page_start+'–'+d.packet_page_end));}
    assert.ok(page.includes(a.packetArchiveUrl));assert.ok(page.indexOf('<h2>Action</h2>')<page.indexOf('<h2>Consent</h2>'));
    assert.doesNotMatch(page,/\b(?:CONFIG|GROUPS|MINUTESURL|LABEL|COUNT)\b/);
    assert.equal((page.match(/data-document-url=/g)||[]).length,count+2);
  }
});

test('March 18 retains all reviewed outcomes, page links, source limitations and the supplied video',()=>{
  const reviewed=JSON.parse(read('data/council/2025-03-18-interactive-agenda.json')),page=read('docs/briefings/2025-03-18-sources.html');
  assert.equal(reviewed.items.length,36);assert.match(reviewed.videoUrl,/UdHDF5Q8o3U/);
  for(const item of reviewed.items){assert.ok(page.includes(`id="item-${item.item.toLowerCase().replace('.','-')}"`));assert.ok(page.includes(`data-minutes-page="${item.page}"`));}
  assert.match(page,/Minutes record:/);assert.match(page,/budgeted \$100,000/);assert.match(page,/request was \$350,000/);
  assert.match(page,/caption track was not retrieved/);assert.doesNotMatch(page,/Complete agenda packets and item attachments are not inventoried/);
  assert.match(read('scripts/build_video_interactive_agendas.py'),/build_page\(date\)/);
});

test('The meeting catalog and library retain the upgraded agendas without a batch section',()=>{
  const context=vm.createContext({window:{}});vm.runInContext(read('docs/council-meeting-sources.js'),context);vm.runInContext(read('docs/documents/library-index.js'),context);
  const overview=read('docs/council-intelligence.html');assert.equal((overview.match(/id="spring-2025-agendas"/g)||[]).length,0);
  for(const [date] of dates){const a=load(date),row=context.window.BI_COUNCIL_MEETING_SOURCES.find(r=>r.date===date);assert.equal(row.interactiveAgenda,`briefings/${date}-sources.html`);assert.equal(row.packet,a.packetArchiveUrl);for(const doc of a.documents)assert.ok(context.window.BI_RESEARCH_LIBRARY.some(r=>r.url===doc.archiveUrl&&r.item===doc.item),doc.archiveUrl);}
  assert.equal(context.window.BI_COUNCIL_MEETING_SOURCES.find(r=>r.date==='2025-03-18').video,'https://www.youtube.com/watch?v=UdHDF5Q8o3U');
});

test('shared document control opens an attachment in the same modal and updates its fallback URL',()=>{
  const element=()=>({value:'',events:{},hidden:false,addEventListener(n,f){this.events[n]=f;}});
  const els=Object.fromEntries(['agenda-search','agenda-section','agenda-count','agenda-empty','viewer-dialog','viewer-frame','viewer-title','viewer-close','viewer-original'].map(id=>['#'+id,element()]));
  els['#agenda-section'].value='all';els['#agenda-config']={textContent:JSON.stringify({date:'2025-03-04',minutesUrl:'https://documents.beaumontintelligence.com/official-documents/2025-03-04/council-minutes.pdf'})};
  const events={};els['#viewer-dialog'].showModal=()=>els['#viewer-dialog'].open=true;
  vm.runInNewContext(read('docs/briefings/video-agendas.js'),{document:{querySelector:s=>els[s],querySelectorAll:()=>[],addEventListener(n,f){events[n]=f;},getElementById:()=>null},window:{addEventListener(){}},location:{href:'https://beaumontintelligence.com/briefings/2025-03-04-sources.html',hash:''},URL,URLSearchParams});
  const d=load('2025-03-04').documents.find(r=>r.item==='J.5');
  events.click({target:{closest:selector=>selector==='[data-document-url]'?{dataset:{documentUrl:d.archiveUrl,title:d.title}}:null}});
  const query=new URLSearchParams(els['#viewer-frame'].src.split('?')[1]);assert.equal(query.get('url'),d.archiveUrl);assert.equal(query.has('page'),false);assert.equal(els['#viewer-original'].href,els['#viewer-frame'].src);assert.equal(els['#viewer-dialog'].open,true);
});
