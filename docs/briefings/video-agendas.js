(() => {
  const config=JSON.parse(document.querySelector('#agenda-config').textContent);
  const rows=[...document.querySelectorAll('.agenda-record')],sections=[...document.querySelectorAll('.agenda-section')];
  const search=document.querySelector('#agenda-search'),filter=document.querySelector('#agenda-section'),count=document.querySelector('#agenda-count');
  const dialog=document.querySelector('#viewer-dialog'),frame=document.querySelector('#viewer-frame'),title=document.querySelector('#viewer-title');
  function render(){
    const term=search.value.trim().toLowerCase();
    rows.forEach(row=>{row.hidden=(filter.value!=='all'&&row.dataset.section!==filter.value)||(term&&!row.textContent.toLowerCase().includes(term));if(term&&!row.hidden)row.open=true;});
    sections.forEach(section=>section.hidden=[...section.querySelectorAll('.agenda-record')].every(row=>row.hidden));
    const visible=rows.filter(row=>!row.hidden).length;
    count.textContent=`${visible} of ${rows.length} agenda entries shown`;
    document.querySelector('#agenda-empty').hidden=visible!==0;
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-minutes-page]')||event.target.closest('[data-document-url]');if(!button)return;
    title.textContent=button.dataset.title;
    const source=button.dataset.documentUrl||config.minutesUrl;
    const query=new URLSearchParams({url:source,title:button.dataset.title,returnUrl:new URL(config.date+'-sources.html',location.href).href,returnLabel:'Back to interactive agenda'});
    if(button.dataset.minutesPage)query.set('page',button.dataset.minutesPage);
    const destination='../documents/viewer.html?'+query;
    const original=document.querySelector('#viewer-original');if(original){original.href=destination;original.textContent='Open viewer in a new tab ↗';}
    frame.src=destination;
    dialog.showModal();
  });
  document.querySelector('#viewer-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{frame.src='about:blank';});
  function revealHash(){const row=document.getElementById(location.hash.slice(1));if(row?.matches('.agenda-record')){search.value='';filter.value='all';render();row.open=true;row.scrollIntoView();}}
  search.addEventListener('input',render);filter.addEventListener('change',render);window.addEventListener('hashchange',revealHash);
  render();revealHash();
})();
