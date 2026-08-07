(() => {
  const index = Array.isArray(window.BI_SEARCH_INDEX) ? window.BI_SEARCH_INDEX : [];
  const form = document.getElementById('site-search-form');
  const input = document.getElementById('site-search-input');
  const results = document.getElementById('site-search-results');
  const title = document.getElementById('search-results-title');
  const filters = [...document.querySelectorAll('[data-filter]')];
  let activeFilter = 'all';
  let currentQuery = '';

  const norm = value => (value || '').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').replace(/[’']/g, '')
    .replace(/[^a-z0-9]+/g, ' ').trim();

  const esc = value => String(value).replace(/[&<>'"]/g, char => ({
    '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'
  }[char]));

  const categoryWeight = {
    'Intelligence Center':28,'Council Briefing':24,'Council Intelligence':20,
    'Project Page':16,'Official Document':12,'Research Library':10,
    'Page':8,'Research Record':2
  };

  const aliases = {
    'cfd':['mello roos','community facilities district'],
    'mello roos':['cfd','community facilities district'],
    'pennsylvania underpass':['pennsylvania grade separation'],
    'railroad underpass':['pennsylvania grade separation'],
    'animal services':['animal control'],
    'wrcog':['western riverside council of governments']
  };

  function expand(query) {
    const normalized = norm(query);
    const terms = normalized.split(/\s+/).filter(Boolean);
    const phrases = [normalized];
    Object.entries(aliases).forEach(([key, values]) => {
      if (normalized.includes(key)) phrases.push(...values);
    });
    return {terms, phrases:[...new Set(phrases.map(norm).filter(Boolean))]};
  }

  function score(item, search) {
    const t = norm(item.title);
    const d = norm(item.description);
    const c = norm(item.category);
    const x = norm(item.text);
    const a = norm((item.aliases || []).join(' '));
    const all = `${t} ${d} ${a} ${x}`;
    let total = categoryWeight[item.category] || 0;

    search.phrases.forEach(phrase => {
      if (t === phrase) total += 180;
      else if (t.startsWith(phrase)) total += 110;
      else if (t.includes(phrase)) total += 75;
      if (a.includes(phrase)) total += 55;
      if (d.includes(phrase)) total += 35;
      if (x.includes(phrase)) total += 15;
    });

    search.terms.forEach(term => {
      if (t.split(' ').includes(term)) total += 30;
      else if (t.includes(term)) total += 18;
      if (c.includes(term)) total += 10;
      if (a.includes(term)) total += 14;
      if (d.includes(term)) total += 8;
      const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const count = (x.match(new RegExp(`\\b${escaped}`, 'g')) || []).length;
      total += Math.min(count, 6) * 2;
    });

    if (search.terms.every(term => all.includes(term))) total += 45;
    if (item.category === 'Intelligence Center') total += 20;
    if (item.category === 'Council Briefing') total += 14;
    return total;
  }

  const isDocument = item =>
    item.category === 'Official Document' || item.category === 'Research Record';

  function render(query) {
    currentQuery = query.trim();
    const search = expand(currentQuery);
    const params = new URLSearchParams(location.search);
    if (currentQuery) params.set('q', currentQuery); else params.delete('q');
    history.replaceState(null, '', location.pathname + (params.toString() ? `?${params}` : ''));

    if (!search.terms.length) {
      title.textContent = 'Search Beaumont Intelligence';
      results.innerHTML = '<div class="empty">Enter a project, meeting, agency, funding source, or document title.</div>';
      return;
    }

    let matches = index.map(item => ({...item,_score:score(item,search)}))
      .filter(item => item._score > 12);

    if (activeFilter === 'page') matches = matches.filter(item => !isDocument(item));
    if (activeFilter === 'document') matches = matches.filter(isDocument);

    const seenUrls = new Set();
    const seenTitles = new Set();
    matches = matches.filter(item => {
      const titleKey = `${norm(item.title)}|${item.category}`;
      if (seenUrls.has(item.url) || seenTitles.has(titleKey)) return false;
      seenUrls.add(item.url);
      seenTitles.add(titleKey);
      return true;
    });

    matches.sort((a,b) =>
      b._score-a._score ||
      (categoryWeight[b.category]||0)-(categoryWeight[a.category]||0) ||
      a.title.localeCompare(b.title)
    );

    title.textContent = `${matches.length} result${matches.length===1?'':'s'} for “${currentQuery}”`;

    if (!matches.length) {
      results.innerHTML = '<div class="empty"><strong>No results found.</strong><span>Try a shorter project name, meeting date, agency, funding source, or document title.</span></div>';
      return;
    }

    results.innerHTML = matches.slice(0,60).map(item => `
      <article class="search-result-card">
        <div class="search-result-meta"><span>${esc(item.category)}</span></div>
        <h3><a href="${esc(item.url)}">${esc(item.title)}</a></h3>
        <p>${esc(item.description || 'Open this Beaumont Intelligence record.')}</p>
        <a class="text-link" href="${esc(item.url)}">Open result →</a>
      </article>`).join('');
  }

  form?.addEventListener('submit', event => {
    event.preventDefault();
    render(input.value);
  });

  filters.forEach(button => button.addEventListener('click', () => {
    filters.forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    activeFilter = button.dataset.filter;
    render(currentQuery);
  }));

  const initial = new URLSearchParams(location.search).get('q') || '';
  input.value = initial;
  render(initial);
})();