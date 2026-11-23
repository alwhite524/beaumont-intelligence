(() => {
  const year = document.getElementById('budget-detail-year');
  if (!year) return;
  const documentSelect = document.getElementById('budget-detail-document');
  const section = document.getElementById('budget-detail-section');
  const search = document.getElementById('budget-detail-search');
  const results = document.getElementById('budget-detail-results');
  const status = document.getElementById('budget-detail-status');
  const more = document.getElementById('budget-detail-more');
  const cache = new Map();
  let data, request = 0, limit = 8;
  const fy = value => `FY ${value - 1}–${String(value).slice(-2)}`;
  const node = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  const option = (value, text) => new Option(text, value);
  function sourceLink(text, source, page = 1) {
    const a = node('a', text);
    const params = new URLSearchParams({pdf: '../' + source, title: `${fy(data.year)} budget`, page, returnUrl: '../budget-budgets.html?year=' + data.year + '#budget-detail', returnLabel: 'Budget details'});
    a.href = 'documents/viewer.html?' + params;
    return a;
  }
  function clearReaders() { results.querySelectorAll('.budget-page-reader').forEach(reader=>window.BIPdfReader.clear(reader)); }
  function render() {
    if (!data) return;
    const query = search.value.trim().toLocaleLowerCase().replace(/\s+/g, ' ');
    const matches = data.documents.flatMap((doc, i) => doc.pages.map(page => ({...page, doc, index:i})))
      .filter(p => (documentSelect.value === '' || p.index === Number(documentSelect.value)) && (!section.value || (p.sections || [p.section]).includes(section.value)) && (!query || p.text.toLocaleLowerCase().replace(/\s+/g, ' ').includes(query)));
    status.textContent = `${fy(data.year)} · ${matches.length} matching pages · Showing ${Math.min(limit, matches.length)}`;
    const cards = matches.slice(0, limit).map((p, i) => {
      const card = node('details', undefined, 'budget-detail-page');
      card.open = i === 0;
      const summary = node('summary');
      summary.append(node('strong', p.section), node('span', `${p.doc.title} · PDF page ${p.page}`));
      const actions = node('p'); actions.append(sourceLink('View original page', p.doc.source, p.page));
      const reader = node('div', undefined, 'budget-page-reader');
      let opened = false;
      card.addEventListener('toggle', () => {
        if (card.open && !opened) {opened = true; window.BIPdfReader.open(reader, p.doc.source, p.doc.title, {startPage:p.page, endPage:p.page});}
        if (!card.open && opened) {window.BIPdfReader.clear(reader);opened = false;}
      });
      const extracted = node('details', undefined, 'budget-extracted-text');
      extracted.append(node('summary','Searchable text (check original for table columns)'));
      const text = node('pre', p.text.replace(/[^\S\n]+/g, ' ') || 'This page contains graphics or scanned content. Use the original page to read it.');
      text.tabIndex = 0; text.setAttribute('aria-label', `${p.section}, page ${p.page}; scroll horizontally for all columns`);
      extracted.append(text);
      card.append(summary, actions, reader, extracted);
      return card;
    });
    clearReaders(); results.replaceChildren(...cards);
    if (!matches.length) results.append(node('p', data.documents.length ? 'No pages match. Try another department, account number, or search term.' : 'Searchable detail is not yet available for this year. Use the City source above.'));
    more.hidden = matches.length <= limit;
  }
  function updateSections() {
    const documents = data.documents.filter((_,i)=>documentSelect.value === '' || i === Number(documentSelect.value));
    const sections = [...new Set(documents.flatMap(doc=>doc.pages.flatMap(p=>p.sections || [p.section])))];
    section.replaceChildren(option('', 'All sections'), ...sections.map(s=>option(s,s)));
    limit = 8; render();
  }
  async function loadYear() {
    const token = ++request;
    data = null;
    clearReaders(); results.replaceChildren(); status.textContent = `Loading ${fy(Number(year.value))} details…`;
    documentSelect.disabled = section.disabled = search.disabled = true;
    more.hidden = true;
    document.getElementById('budget-detail-sources').replaceChildren();
    document.getElementById('budget-detail-note').textContent = '';
    const url = new URL(location.href); url.searchParams.set('year',year.value); history.replaceState(null,'',url);
    try {
      let loaded = cache.get(year.value);
      if (!loaded) {
        const response = await fetch(`budget-details/${year.value}.json?v=20261122`);
        if (!response.ok) throw Error('Could not load budget details');
        loaded = await response.json(); cache.set(year.value, loaded);
      }
      if (token !== request) return;
      data = loaded;
      documentSelect.replaceChildren(option('', 'All documents'), ...data.documents.map((d,i)=>option(i,d.title)));
      document.getElementById('budget-detail-title').textContent = `${fy(data.year)} budget details`;
      document.getElementById('budget-detail-note').textContent = data.notice || 'Search the adopted budget book by department, fund, service, or account. Extracted text may omit graphics or alter table spacing. Check the original page when citing figures.';
      const sources = document.getElementById('budget-detail-sources');
      const book = data.book || (data.documents.length===1 && data.documents[0].source);
      if (book) sources.append(sourceLink('Open full budget book', book));
      if (data.externalSource) { const a=node('a','Open City budget source'); a.href=data.externalSource; sources.append(a); }
      documentSelect.disabled = section.disabled = search.disabled = !data.documents.length;
      search.value = ''; updateSections();
      const summaryYear = document.getElementById('budget-year');
      if ([...summaryYear.options].some(o=>o.value===year.value) && summaryYear.value!==year.value) {summaryYear.value=year.value; summaryYear.dispatchEvent(new Event('change'));}
    } catch {
      if(token !== request) return;
      status.textContent = 'Budget details could not be loaded. Please retry.';
      const retry=node('button','Retry');retry.type='button';retry.addEventListener('click',loadYear);results.append(retry);
    }
  }
  year.replaceChildren(...Array.from({length:7},(_,i)=>2027-i).map(y=>option(y,fy(y))));
  const requested = new URLSearchParams(location.search).get('year');
  year.value = [...year.options].some(o=>o.value===requested) ? requested : '2027';
  year.addEventListener('change',loadYear);
  documentSelect.addEventListener('change',updateSections);
  section.addEventListener('change',()=>{limit=8;render();});
  search.addEventListener('input',()=>{limit=8;render();});
  more.addEventListener('click',()=>{limit+=8;render();});
  document.getElementById('budget-year').addEventListener('change',event=>{if(year.value!==event.target.value){year.value=event.target.value;loadYear();}});
  loadYear();
})();
