(() => {
  const results = document.getElementById('budget-detail-results');
  if (!results) return;
  const byId=id=>document.getElementById(id);
  const fund=byId('budget-table-fund'), department=byId('budget-detail-section'), type=byId('budget-table-type'), search=byId('budget-detail-search'), sort=byId('budget-table-sort'), direction=byId('budget-table-direction'), more=byId('budget-detail-more');
  const status=byId('budget-detail-status');
  const currency=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2});
  const deltaCurrency=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',signDisplay:'exceptZero'});
  const amountLabels=['Original budget','Current budget','Delta'];
  const archiveOrigin='https://documents.beaumontintelligence.com/';
  const columns=[['account','Account'],['description','Description'],['fund','Fund'],['department','Department'],['type','Type'],['original','Original budget'],['current','Current budget']];
  const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  let data,limit=50,descending=false;
  const filters=[fund,department,type,search,sort];
  const controls=[...filters,direction];
  const filterKey='beaumont:budget-account-filters';
  const accountFragment=account=>`#budget-account-${account}`;
  function restoreAccount(){
    const id=location.hash.slice(1);
    if(!id.startsWith('budget-account-')) return;
    const card=byId(id);
    const target=card?.getClientRects().length ? card : byId(id+'-row');
    if(!target) return;
    if(card) card.open=true;
    requestAnimationFrame(()=>{
      target.focus({preventScroll:true});
      target.scrollIntoView({block:'start'});
    });
  }
  function link(label,source,page=1,account){
    const anchor=node('a',label);
    const params=new URLSearchParams({
      url:new URL(source,archiveOrigin).href,
      title:'FY 2026–2027 budget detail report',
      page,
      returnUrl:'../budget-budgets.html'+(account ? accountFragment(account) : '#budget-detail'),
      returnLabel:'Budget details',
    });
    anchor.href='documents/viewer.html?'+params;
    if(account) anchor.addEventListener('click',()=>{
      history.replaceState(history.state,'',accountFragment(account));
    });
    return anchor;
  }
  function renderCards(rows){
    const cards=node('div',undefined,'budget-account-cards');
    const headings=node('div',undefined,'budget-card-amounts budget-card-headings');
    headings.setAttribute('aria-hidden','true');
    headings.append(...amountLabels.map(label=>node('span',label)));
    cards.append(headings);

    rows.forEach(row=>{
      const card=node('details',undefined,'budget-account-card');
      card.id=accountFragment(row.account).slice(1);
      card.tabIndex=-1;
      const summary=node('summary');
      const title=node('span',row.description,'budget-card-description');
      const amounts=node('span',undefined,'budget-card-amounts');
      const delta=(Math.round(row.current*100)-Math.round(row.original*100))/100;
      const values=[currency.format(row.original),currency.format(row.current),deltaCurrency.format(delta)];
      values.forEach((value,index)=>{
        const amount=node('span');
        amount.append(node('span',amountLabels[index]+': ','visually-hidden'),value);
        amounts.append(amount);
      });
      summary.append(title,amounts);

      const details=node('dl',undefined,'budget-card-details');
      const fields=[['Account',row.account],['Fund',row.fund],['Department',row.department],['Type',row.type],['Source',link(`Page ${row.page}`,data.source,row.page,row.account)]];
      fields.forEach(([label,value])=>{
        const definition=node('dd');
        definition.append(value);
        details.append(node('dt',label),definition);
      });
      card.append(summary,details);
      cards.append(card);
    });
    return cards;
  }
  function render(restore=false){
    try {
      const values=Object.fromEntries(filters.map(control=>[control.id,control.value]));
      localStorage.setItem(filterKey,JSON.stringify({...values,descending}));
    } catch { /* Filtering still works without storage. */ }
    const query=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const matches=data.rows.filter(row=>(!fund.value||row.fund===fund.value)&&(!department.value||row.department===department.value)&&(!type.value||row.type===type.value)&&query.every(q=>[row.account,row.description,row.fund,row.department,row.type].join(' ').toLowerCase().includes(q)));
    const key=sort.value;
    matches.sort((a,b)=>{const comparison=typeof a[key]==='number'?a[key]-b[key]:a[key].localeCompare(b[key],undefined,{numeric:true});return (descending?-comparison:comparison)||a.account.localeCompare(b.account);});
    if(restore){
      const index=matches.findIndex(row=>accountFragment(row.account)===location.hash);
      limit=Math.max(limit,Math.ceil((index+1)/50)*50);
    }
    const shown=matches.slice(0,limit);
    status.textContent=`${matches.length.toLocaleString()} matching ${matches.length===1?'account':'accounts'} · Showing ${shown.length.toLocaleString()} of ${data.rows.length.toLocaleString()} accounts`;
    direction.textContent=descending?'Descending':'Ascending';direction.setAttribute('aria-label',`Sort direction: ${descending?'descending':'ascending'}. Change direction`);
    const table=node('table',undefined,'finance-table budget-account-table');
    const caption=table.createCaption();caption.textContent='FY 2026–2027 budget accounts';caption.className='visually-hidden';
    const header=table.createTHead().insertRow();
    columns.forEach(([field,label])=>{const th=node('th');th.scope='col';th.setAttribute('aria-sort',field===key?(descending?'descending':'ascending'):'none');const button=node('button',label+(field===key?(descending?' ▼':' ▲'):''));button.type='button';button.addEventListener('click',()=>{descending=field===sort.value?!descending:false;sort.value=field;limit=50;render();});th.append(button);header.append(th);});
    const sourceHead=node('th','Source');sourceHead.scope='col';header.append(sourceHead);
    const body=table.createTBody();
    shown.forEach(row=>{const tr=body.insertRow();tr.id=accountFragment(row.account).slice(1)+'-row';tr.tabIndex=-1;columns.forEach(([field,label])=>{const cell=node(field==='account'?'th':'td',typeof row[field]==='number'?currency.format(row[field]):row[field]);if(field==='account')cell.scope='row';cell.dataset.label=label;tr.append(cell);});const cell=tr.insertCell();cell.dataset.label='Source';cell.append(link(`Page ${row.page}`,data.source,row.page,row.account));});
    results.replaceChildren(table);
    if(shown.length)results.append(renderCards(shown));
    if(!matches.length)results.append(node('p','No accounts match. Try another search or clear the filters.'));
    more.hidden=shown.length===matches.length;
    if(restore) restoreAccount();
    const totals=byId('budget-table-totals');totals.replaceChildren(...['Revenue','Expense'].map(kind=>{const amount=matches.filter(r=>r.type===kind).reduce((sum,r)=>sum+Math.round(r.current*100),0)/100;const card=node('div');card.append(node('span',`Matching ${kind.toLowerCase()} budget`),node('strong',currency.format(amount)));return card;}));
  }
  function updateDepartments(){const previous=department.value;const values=[...new Set(data.rows.filter(r=>!fund.value||r.fund===fund.value).map(r=>r.department))].sort();department.replaceChildren(new Option('All departments',''),...values.map(v=>new Option(v,v)));if(values.includes(previous))department.value=previous;}
  async function load(){
    controls.forEach(c=>c.disabled=true);status.textContent='Loading FY 2026–2027 budget accounts…';more.hidden=true;
    try{
      const response=await fetch('budget-details/2027-table.json?v=20261122-table');if(!response.ok)throw Error('Unavailable');data=await response.json();
      const generalFund='100 - GENERAL FUND';
      const funds=[...new Set(data.rows.map(r=>r.fund))].sort();
      fund.replaceChildren(new Option('All funds',''),...funds.map(value=>new Option(value===generalFund?'100 - General Fund':value,value)));
      if(funds.includes(generalFund)) fund.value=generalFund;
      sort.replaceChildren(...columns.map(([key,label])=>new Option(label,key)));sort.value='account';
      let saved={};
      try {
        saved=JSON.parse(localStorage.getItem(filterKey))??{};
      } catch { /* Keep the default filters when storage is unavailable. */ }
      for(const control of filters){
        if(control===department) updateDepartments();
        const value=saved[control.id];
        if(typeof value==='string' && (control===search || Array.from(control.options).some(option=>option.value===value))){
          control.value=value;
        }
      }
      if(typeof saved.descending==='boolean') descending=saved.descending;
      byId('budget-detail-note').textContent=data.basis;
      byId('budget-detail-sources').replaceChildren(link('Open source detail report',data.source));
      window.BIPdfReader.open(byId('budget-book-reader'),new URL(data.book,archiveOrigin).href,'FY 2026–2027 budget book');
      controls.forEach(c=>c.disabled=false);render(true);
    }catch{status.textContent='Budget accounts could not be loaded.';const retry=node('button','Retry');retry.type='button';retry.addEventListener('click',()=>{results.replaceChildren();load();});results.replaceChildren(retry);}
  }
  fund.addEventListener('change',()=>{updateDepartments();limit=50;render();});
  [department,type,sort].forEach(control=>control.addEventListener('change',()=>{limit=50;render();}));
  search.addEventListener('input',()=>{limit=50;render();});direction.addEventListener('click',()=>{descending=!descending;limit=50;render();});more.addEventListener('click',()=>{limit+=50;render();});
  window.addEventListener('pageshow',event=>{if(event.persisted) restoreAccount();});
  load();
})();
