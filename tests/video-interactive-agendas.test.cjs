const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const read=p=>fs.readFileSync(p,'utf8');
const entries=[['2025-03-18','UdHDF5Q8o3U',36],['2024-04-02','mJsVkhQDrVo',30],['2024-06-04','bwWuHfdi07k',27]];
const load=date=>JSON.parse(read(`data/council/${date}-interactive-agenda.json`));

test('each supplied video has a complete minutes-backed agenda with valid page references',()=>{
  const register=JSON.parse(read('data/council/minutes-register.json')).documents;
  for(const [date,id,count] of entries){
    const data=load(date),minutes=register.find(r=>r.date===date&&r.kind==='regular');
    assert.equal(data.videoUrl,'https://www.youtube.com/watch?v='+id);
    assert.equal(data.items.length,count);assert.equal(new Set(data.items.map(i=>i.item)).size,count);
    assert.equal(data.minutesUrl,minutes.url);assert.equal(data.minutesSha256,minutes.sha256);
    assert.equal(data.minutesPageCount,minutes.textPages.length);
    const page=read(`docs/briefings/${date}-sources.html`);
    assert.match(page,/caption track was not retrieved/);assert.match(page,/Clock times printed in the minutes are not video offsets/);
    assert.ok(page.includes('youtube-nocookie.com/embed/'+id));
    for(const item of data.items){assert.ok(item.page>=1&&item.page<=data.minutesPageCount);assert.equal(item.timestampSeconds,null);assert.ok(page.includes(`id="item-${item.item.toLowerCase().replace('.','-')}"`));}
    assert.doesNotMatch(page,/\b(?:LABEL|COUNT|GROUPS|CONFIG|MINUTESURL)\b/);
    assert.ok(page.indexOf('<h2>Action</h2>')<page.indexOf('<h2>Consent</h2>'));
  }
});

test('requests, contingent steps and missing vote tallies are not turned into broader approvals',()=>{
  const march=load('2025-03-18');
  const cherry=march.items.find(i=>i.item==='J.5').outcome;
  assert.match(cherry,/request was \$350,000/);assert.match(cherry,/budgeted \$100,000/);
  assert.match(march.items.find(i=>i.item==='J.10').outcome,/4–0/);
  assert.match(march.items.find(i=>i.item==='J.11').outcome,/not a construction award/);
  assert.match(march.items.find(i=>i.item==='J.2').outcome,/requires verification/);
  const june=load('2024-06-04');
  assert.match(june.items.find(i=>i.item==='G.1').outcome,/do not print a separate vote tally/);
  assert.match(june.items.find(i=>i.item==='G.9').outcome,/separately/);
  assert.match(june.items.find(i=>i.item==='J.2').outcome,/not interchange construction/);
});

test('Council overview links to the meeting catalog and all three agendas are in the catalog and Research Library',()=>{
  const councilOverview=read('docs/council-intelligence.html');
  assert.match(councilOverview,/href="council-meeting-sources\.html"/);
  assert.doesNotMatch(councilOverview,/id="video-agenda-records"/);
  const context=vm.createContext({window:{}});
  vm.runInContext(read('docs/council-meeting-sources.js'),context);
  vm.runInContext(read('docs/documents/library-index.js'),context);
  for(const [date,id,count] of entries){
    const row=context.window.BI_COUNCIL_MEETING_SOURCES.find(r=>r.date===date);
    assert.equal(row.video,'https://www.youtube.com/watch?v='+id);assert.equal(row.interactiveAgenda,`briefings/${date}-sources.html`);assert.ok(row.minutes);
    assert.equal(context.window.BI_RESEARCH_LIBRARY.filter(r=>r.date===date&&r.type==='Agenda item'&&r.url.includes(`${date}-sources.html#item-`)).length,count);
  }
});

test('shared navigation filters sections and outcomes, reveals anchors and opens exact minutes pages',()=>{
  const make=(section,text)=>({dataset:{section},textContent:text,hidden:false,open:false,matches:s=>s==='.agenda-record',scrollIntoView(){this.scrolled=true;}});
  const rows=[make('Consent','Warrants approved'),make('Action','Cherry Festival sponsorship $100,000'),make('Action','Reject wastewater bids')];
  const element=()=>({events:{},value:'',hidden:false,addEventListener(n,f){this.events[n]=f;}});
  const els=Object.fromEntries(['agenda-search','agenda-section','agenda-count','agenda-empty','viewer-dialog','viewer-frame','viewer-title','viewer-close'].map(id=>['#'+id,element()]));
  els['#agenda-section'].value='all';
  els['#agenda-config']={textContent:JSON.stringify({date:'2025-03-18',label:'March 18, 2025',minutesUrl:load('2025-03-18').minutesUrl})};
  const sections=['Consent','Action'].map(s=>({querySelectorAll:()=>rows.filter(r=>r.dataset.section===s)}));
  const events={};els['#viewer-dialog'].showModal=()=>els['#viewer-dialog'].open=true;
  els['#viewer-dialog'].close=()=>{els['#viewer-dialog'].open=false;els['#viewer-dialog'].events.close();};
  const location={href:'https://beaumontintelligence.com/briefings/2025-03-18-sources.html',hash:''};
  vm.runInNewContext(read('docs/briefings/video-agendas.js'),{document:{querySelector:s=>els[s],querySelectorAll:s=>s==='.agenda-record'?rows:sections,addEventListener(n,f){events[n]=f;},getElementById:id=>id==='item-j-5'?rows[1]:null},window:{addEventListener(n,f){events[n]=f;}},location,URL,URLSearchParams});
  assert.equal(els['#agenda-count'].textContent,'3 of 3 agenda entries shown');
  els['#agenda-section'].value='Action';els['#agenda-section'].events.change();assert.equal(rows[0].hidden,true);
  els['#agenda-search'].value='100,000';els['#agenda-search'].events.input();assert.equal(els['#agenda-count'].textContent,'1 of 3 agenda entries shown');assert.equal(rows[1].open,true);
  els['#agenda-search'].value='absent';els['#agenda-search'].events.input();assert.equal(els['#agenda-empty'].hidden,false);
  location.hash='#item-j-5';events.hashchange();assert.equal(rows[1].scrolled,true);assert.equal(els['#agenda-section'].value,'all');
  events.click({target:{closest:()=>({dataset:{minutesPage:'6',title:'Cherry Festival minutes'}})}});
  const query=new URLSearchParams(els['#viewer-frame'].src.split('?')[1]);assert.equal(query.get('page'),'6');assert.equal(query.get('url'),load('2025-03-18').minutesUrl);assert.equal(els['#viewer-dialog'].open,true);
  els['#viewer-close'].events.click();assert.equal(els['#viewer-frame'].src,'about:blank');
});
