(() => {
  const results = document.getElementById('budget-detail-results');
  if (!results) return;
  const byId=id=>document.getElementById(id);
  const fund=byId('budget-table-fund'), department=byId('budget-detail-section'), type=byId('budget-table-type'), search=byId('budget-detail-search'), sort=byId('budget-table-sort'), direction=byId('budget-table-direction'), more=byId('budget-detail-more');
  const status=byId('budget-detail-status');
  const currency=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2});
  const columns=[['account','Account'],['description','Description'],['fund','Fund'],['department','Department'],['type','Type'],['original','Original budget'],['current','Current budget']];
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  let data,limit=50,descending=false;
  const controls=[fund,department,type,search,sort,direction];
  function link(label,source,page=1){const a=node('a',label);a.href='documents/viewer.html?'+new URLSearchParams({pdf:'../'+source,title:'FY 2026–2027 budget',page,returnUrl:'../budget-budgets.html#budget-detail',returnLabel:'Budget details'});return a;}
  function render(){
    const query=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const matches=data.rows.filter(row=>(!fund.value||row.fund===fund.value)&&(!department.value||row.department===department.value)&&(!type.value||row.type===type.value)&&query.every(q=>[row.account,row.description,row.fund,row.department,row.type].join(' ').toLowerCase().includes(q)));
    const key=sort.value;
    matches.sort((a,b)=>{const comparison=typeof a[key]==='number'?a[key]-b[key]:a[key].localeCompare(b[key],undefined,{numeric:true});return (descending?-comparison:comparison)||a.account.localeCompare(b.account);});
    const shown=matches.slice(0,limit);
    status.textContent=`${matches.length.toLocaleString()} matching ${matches.length===1?'account':'accounts'} · Showing ${shown.length.toLocaleString()} of ${data.rows.length.toLocaleString()} accounts`;
    direction.textContent=descending?'Descending':'Ascending';direction.setAttribute('aria-label',`Sort direction: ${descending?'descending':'ascending'}. Change direction`);
    const table=node('table',undefined,'finance-table budget-account-table');
    const caption=table.createCaption();caption.textContent='FY 2026–2027 budget accounts';caption.className='visually-hidden';
    const header=table.createTHead().insertRow();
    columns.forEach(([field,label])=>{const th=node('th');th.scope='col';th.setAttribute('aria-sort',field===key?(descending?'descending':'ascending'):'none');const button=node('button',label+(field===key?(descending?' ▼':' ▲'):''));button.type='button';button.addEventListener('click',()=>{descending=field===sort.value?!descending:false;sort.value=field;limit=50;render();});th.append(button);header.append(th);});
    const sourceHead=node('th','Source');sourceHead.scope='col';header.append(sourceHead);
    const body=table.createTBody();
    shown.forEach(row=>{const tr=body.insertRow();columns.forEach(([field,label])=>{const cell=node(field==='account'?'th':'td',typeof row[field]==='number'?currency.format(row[field]):row[field]);if(field==='account')cell.scope='row';cell.dataset.label=label;tr.append(cell);});const cell=tr.insertCell();cell.dataset.label='Source';cell.append(link(`Page ${row.page}`,data.source,row.page));});
    results.replaceChildren(table);
    if(!matches.length)results.append(node('p','No accounts match. Try another search or clear the filters.'));
    more.hidden=shown.length===matches.length;
    const totals=byId('budget-table-totals');totals.replaceChildren(...['Revenue','Expense'].map(kind=>{const amount=matches.filter(r=>r.type===kind).reduce((sum,r)=>sum+Math.round(r.current*100),0)/100;const card=node('div');card.append(node('span',`Matching ${kind.toLowerCase()} budget`),node('strong',currency.format(amount)));return card;}));
  }
  function updateDepartments(){const previous=department.value;const values=[...new Set(data.rows.filter(r=>!fund.value||r.fund===fund.value).map(r=>r.department))].sort();department.replaceChildren(new Option('All departments',''),...values.map(v=>new Option(v,v)));if(values.includes(previous))department.value=previous;}
  async function load(){
    controls.forEach(c=>c.disabled=true);status.textContent='Loading FY 2026–2027 budget accounts…';more.hidden=true;
    try{
      const response=await fetch('budget-details/2027-table.json?v=20261122-table');if(!response.ok)throw Error('Unavailable');data=await response.json();
      fund.replaceChildren(new Option('All funds',''),...[...new Set(data.rows.map(r=>r.fund))].sort().map(v=>new Option(v,v)));
      sort.replaceChildren(...columns.map(([key,label])=>new Option(label,key)));sort.value='account';
      updateDepartments();byId('budget-detail-note').textContent=data.basis;
      byId('budget-detail-sources').replaceChildren(link('Open source detail report',data.source));
      window.BIPdfReader.open(byId('budget-book-reader'),data.book,'FY 2026–2027 budget book');
      controls.forEach(c=>c.disabled=false);render();
    }catch{status.textContent='Budget accounts could not be loaded.';const retry=node('button','Retry');retry.type='button';retry.addEventListener('click',()=>{results.replaceChildren();load();});results.replaceChildren(retry);}
  }
  fund.addEventListener('change',()=>{updateDepartments();limit=50;render();});
  [department,type,sort].forEach(control=>control.addEventListener('change',()=>{limit=50;render();}));
  search.addEventListener('input',()=>{limit=50;render();});direction.addEventListener('click',()=>{descending=!descending;limit=50;render();});more.addEventListener('click',()=>{limit+=50;render();});
  load();
})();
