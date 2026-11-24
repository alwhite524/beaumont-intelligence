(() => {
  const byId=id=>document.getElementById(id),results=byId('audit-results');if(!results)return;
  const search=byId('audit-search'),statement=byId('audit-statement'),fund=byId('audit-fund'),sort=byId('audit-sort'),direction=byId('audit-direction'),more=byId('audit-more'),status=byId('audit-count');
  const fields=[['statement','Statement'],['section','Section'],['metric','Line item'],['fund','Fund / reporting group'],['amount','Reported amount']];
  const currency=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
  const node=(tag,text)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;};
  let data,descending=false,limit=50;
  function render(){
    const query=search.value.toLowerCase().trim().replace(/\s+/g,' ');
    const rows=data.rows.filter(r=>(!statement.value||r.statement===statement.value)&&(!fund.value||r.fund===fund.value)&&[r.statement,r.section,r.metric,r.fund].join(' ').toLowerCase().replace(/\s+/g,' ').includes(query));
    rows.sort((a,b)=>(descending?-1:1)*(typeof a[sort.value]==='number'?a[sort.value]-b[sort.value]:a[sort.value].localeCompare(b[sort.value],undefined,{numeric:true})));
    const table=node('table');table.className='finance-table audit-table';table.createCaption().textContent='FY 2024–25 audited financial statement values (USD)';
    const head=table.createTHead().insertRow();
    fields.forEach(([key,label])=>{const th=node('th');th.scope='col';th.setAttribute('aria-sort',sort.value===key?(descending?'descending':'ascending'):'none');const button=node('button',label+(sort.value===key?(descending?' ▼':' ▲'):''));button.type='button';button.addEventListener('click',()=>{descending=sort.value===key?!descending:false;sort.value=key;limit=50;render();});th.append(button);head.append(th);});
    const source=node('th','Source');source.scope='col';head.append(source);
    const body=table.createTBody();rows.slice(0,limit).forEach(row=>{const tr=body.insertRow();fields.forEach(([key,label])=>{const td=tr.insertCell();td.dataset.label=label;td.textContent=key==='amount'?currency.format(row.amount):row[key];});const td=tr.insertCell();td.dataset.label='Source';const a=node('a',`Page ${row.page}`);a.href='documents/viewer.html?'+new URLSearchParams({url:'../'+data.source,title:'FY 2024–25 audited financial statements',page:row.page,returnUrl:'../budget-audits.html#audit-details',returnLabel:'Audit details'});td.append(a);});
    results.replaceChildren(table);if(!rows.length)results.append(node('p','No audit values match these filters.'));
    status.textContent=`Showing ${Math.min(limit,rows.length)} of ${rows.length} matching values (${data.rows.length} total). Combined totals and their components are separate rows; do not add them together.`;
    direction.textContent=descending?'Descending':'Ascending';direction.setAttribute('aria-label',`Sort direction: ${descending?'descending':'ascending'}. Change direction`);more.hidden=rows.length<=limit;
  }
  async function load(){
    [search,statement,fund,sort,direction].forEach(c=>c.disabled=true);status.textContent='Loading audited financial values…';more.hidden=true;
    try{const response=await fetch('budget-details/audit-2025-table.json?v=20261122');if(!response.ok)throw Error('Unavailable');data=await response.json();
      for(const [control,key,label] of [[statement,'statement','All statements'],[fund,'fund','All funds and reporting groups']])control.replaceChildren(new Option(label,''),...[...new Set(data.rows.map(r=>r[key]))].sort().map(value=>new Option(value,value)));
      sort.replaceChildren(...fields.map(([key,label])=>new Option(label,key)));sort.value='statement';
      [search,statement,fund,sort,direction].forEach(c=>c.disabled=false);render();
      window.BIPdfReader.open(byId('audit-reader'),data.source,'FY 2024–25 Annual Comprehensive Financial Report');
    }catch{status.textContent='Audit values could not be loaded. Please retry.';const retry=node('button','Retry');retry.type='button';retry.addEventListener('click',load);results.replaceChildren(retry);}
  }
  [statement,fund,sort].forEach(c=>c.addEventListener('change',()=>{limit=50;render();}));search.addEventListener('input',()=>{limit=50;render();});direction.addEventListener('click',()=>{descending=!descending;limit=50;render();});more.addEventListener('click',()=>{limit+=50;render();});load();
})();
