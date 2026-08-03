(() => {
  const index = Array.isArray(window.BI_SEARCH_INDEX) ? window.BI_SEARCH_INDEX : [];
  const form = document.getElementById('site-search-form');
  const input = document.getElementById('site-search-input');
  const results = document.getElementById('site-search-results');
  const title = document.getElementById('search-results-title');
  const filters = [...document.querySelectorAll('[data-filter]')];
  let activeFilter = 'all';
  let currentQuery = '';
  const norm = v => (v || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const esc = v => String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  function score(item, terms) {
    const t=norm(item.title), d=norm(item.description), x=norm(item.text), c=norm(item.category);
    let s=0;
    for (const term of terms) {
      if (t===term) s+=80; else if (t.includes(term)) s+=35;
      if (c.includes(term)) s+=12;
      if (d.includes(term)) s+=10;
      const count=(x.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'g'))||[]).length;
      s+=Math.min(count,8)*2;
    }
    if (terms.every(term => (t+' '+d+' '+x).includes(term))) s+=20;
    return s;
  }
  function render(query) {
    currentQuery=query.trim();
    const terms=norm(currentQuery).split(/\s+/).filter(Boolean);
    const params=new URLSearchParams(location.search);
    if (currentQuery) params.set('q',currentQuery); else params.delete('q');
    history.replaceState(null,'',location.pathname+(params.toString()?'?'+params:''));
    if (!terms.length) { title.textContent='Search Beaumont Intelligence'; results.innerHTML='<div class="empty">Enter a search term above.</div>'; return; }
    let matches=index.map(item=>({...item,_score:score(item,terms)})).filter(item=>item._score>0);
    if (activeFilter==='page') matches=matches.filter(i=>i.category!=='Official Document'&&i.category!=='Research Record');
    if (activeFilter==='document') matches=matches.filter(i=>i.category==='Official Document'||i.category==='Research Record');
    matches.sort((a,b)=>b._score-a._score||a.title.localeCompare(b.title));
    title.textContent=`${matches.length} result${matches.length===1?'':'s'} for “${currentQuery}”`;
    if (!matches.length) { results.innerHTML='<div class="empty"><strong>No results found.</strong><span>Try a project name, meeting date, agency, funding source, or document title.</span></div>'; return; }
    results.innerHTML=matches.slice(0,100).map(item=>`<article class="search-result-card"><div class="search-result-meta"><span>${esc(item.category)}</span><small>Relevance ${item._score}</small></div><h3><a href="${esc(item.url)}">${esc(item.title)}</a></h3><p>${esc(item.description||'Open this Beaumont Intelligence record.')}</p><a class="text-link" href="${esc(item.url)}">Open result →</a></article>`).join('');
  }
  form?.addEventListener('submit',e=>{e.preventDefault();render(input.value);});
  filters.forEach(btn=>btn.addEventListener('click',()=>{filters.forEach(b=>b.classList.remove('active'));btn.classList.add('active');activeFilter=btn.dataset.filter;render(currentQuery);}));
  const initial=new URLSearchParams(location.search).get('q')||''; input.value=initial; render(initial);
})();