(() => {
  const rawIndex = Array.isArray(window.BI_SEARCH_INDEX) ? window.BI_SEARCH_INDEX : [];
  const index = rawIndex.flatMap(item => {
    if (Array.isArray(item?.value)) return item.value;
    return item?.title && item?.url ? [item] : [];
  });
  const form = document.getElementById('site-search-form');
  const input = document.getElementById('site-search-input');
  const results = document.getElementById('site-search-results');
  const title = document.getElementById('search-results-title');
  const filters = [...document.querySelectorAll('[data-filter]')];

  let activeFilter = 'all';
  let currentQuery = '';

  const norm = value => (value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[’']/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

  const esc = value => String(value).replace(/[&<>'"]/g, char => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'
  }[char]));

  const STOP_WORDS = new Set([
    'a','an','and','are','as','at','be','by','for','from','in','is',
    'of','on','or','the','to','with'
  ]);

  const categoryWeight = {
    'Intelligence Center': 28,
    'Council Briefing': 24,
    'Council Intelligence': 20,
    'Project Page': 16,
    'Official Document': 12,
    'Research Library': 10,
    'Page': 8,
    'Research Record': 2
  };

  // Civic-language aliases. These supplement matching; they never make a
  // record a result by themselves unless the record actually contains one
  // of the expanded phrases/terms.
  const QUERY_ALIASES = {
    'cfd': ['mello roos', 'community facilities district'],
    'mello roos': ['cfd', 'community facilities district'],
    'pennsylvania underpass': ['pennsylvania grade separation'],
    'railroad underpass': ['pennsylvania grade separation'],
    'animal services': ['animal control'],
    'wrcog': ['western riverside council of governments'],
    'measure a': ['transportation funding', 'rctc', 'wrcog']
  };

  function expandQuery(query) {
    const phrase = norm(query);
    const rawTerms = phrase.split(/\s+/).filter(Boolean);

    // Single-letter/common words can never independently qualify a record.
    const significantTerms = rawTerms.filter(term =>
      term.length >= 2 && !STOP_WORDS.has(term)
    );

    const aliases = [];
    Object.entries(QUERY_ALIASES).forEach(([key, values]) => {
      if (phrase === key || phrase.includes(key)) aliases.push(...values);
    });

    return {
      phrase,
      rawTerms,
      significantTerms,
      aliasPhrases: [...new Set(aliases.map(norm).filter(Boolean))]
    };
  }

  function fields(item) {
    return {
      title: norm(item.title),
      description: norm(item.description),
      category: norm(item.category),
      aliases: norm((item.aliases || []).join(' ')),
      body: norm(item.text)
    };
  }

  function containsWhole(text, term) {
    if (!term) return false;
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`(^|\\s)${escaped}(?=\\s|$)`).test(text);
  }

  function evaluate(item, search) {
    const f = fields(item);
    const highValue = `${f.title} ${f.description} ${f.aliases}`;
    const all = `${highValue} ${f.body}`;

    const exactPhrase = search.phrase.length >= 2 && all.includes(search.phrase);
    const exactPhraseHigh = search.phrase.length >= 2 && highValue.includes(search.phrase);

    const sigMatches = search.significantTerms.filter(term => containsWhole(all, term));
    const allSignificant = search.significantTerms.length > 0 &&
      sigMatches.length === search.significantTerms.length;

    const highValueTermMatch = search.significantTerms.some(term =>
      containsWhole(highValue, term)
    );

    const matchedAliasPhrases = search.aliasPhrases.filter(alias =>
      all.includes(alias)
    );

    /*
      MATCH GATE:
      Category weights are applied only AFTER a record proves relevance.
      This fixes Search-102's central bug where a high category weight alone
      made unrelated records appear as results.
    */
    const directMatch = exactPhrase || (allSignificant && highValueTermMatch);
    const aliasMatch = matchedAliasPhrases.length > 0;

    if (!directMatch && !aliasMatch) return null;

    let score = categoryWeight[item.category] || 0;

    if (exactPhraseHigh) score += 260;
    else if (exactPhrase) score += 170;

    search.significantTerms.forEach(term => {
      if (containsWhole(f.title, term)) score += 70;
      if (containsWhole(f.aliases, term)) score += 55;
      if (containsWhole(f.description, term)) score += 35;
      if (containsWhole(f.category, term)) score += 18;

      const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const count = (f.body.match(new RegExp(`(^|\\s)${escaped}(?=\\s|$)`, 'g')) || []).length;
      score += Math.min(count, 5) * 4;
    });

    if (allSignificant) score += 70;
    if (highValueTermMatch) score += 35;

    matchedAliasPhrases.forEach(alias => {
      if (f.title.includes(alias)) score += 65;
      else if (highValue.includes(alias)) score += 42;
      else score += 20;
    });

    if (item.category === 'Intelligence Center') score += 18;
    if (item.category === 'Council Briefing') score += 12;

    return {
      ...item,
      _score: score,
      _matchType: exactPhrase ? 'exact' : (directMatch ? 'direct' : 'related')
    };
  }

  const isDocument = item =>
    item.category === 'Official Document' || item.category === 'Research Record';

  function render(query) {
    currentQuery = query.trim();
    const search = expandQuery(currentQuery);
    const params = new URLSearchParams(location.search);

    if (currentQuery) params.set('q', currentQuery);
    else params.delete('q');

    history.replaceState(
      null,
      '',
      location.pathname + (params.toString() ? `?${params}` : '')
    );

    if (!search.phrase) {
      title.textContent = 'Search Beaumont Intelligence';
      results.innerHTML =
        '<div class="empty">Enter a project, meeting, agency, funding source, or document title.</div>';
      return;
    }

    let matches = index
      .map(item => evaluate(item, search))
      .filter(Boolean);

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

    const matchPriority = { exact: 3, direct: 2, related: 1 };

    matches.sort((a, b) =>
      (matchPriority[b._matchType] || 0) - (matchPriority[a._matchType] || 0) ||
      b._score - a._score ||
      (categoryWeight[b.category] || 0) - (categoryWeight[a.category] || 0) ||
      a.title.localeCompare(b.title)
    );

    title.textContent =
      `${matches.length} result${matches.length === 1 ? '' : 's'} for “${currentQuery}”`;

    if (!matches.length) {
      results.innerHTML =
        '<div class="empty"><strong>No strong matches found.</strong><span>Try a project name, meeting date, agency, funding source, or a shorter phrase.</span></div>';
      return;
    }

    results.innerHTML = matches.slice(0, 60).map(item => `
      <article class="search-result-card">
        <div class="search-result-meta">
          <span>${esc(item.category)}</span>
          ${item._matchType === 'related' ? '<span>Related term</span>' : ''}
        </div>
        <h3><a href="${esc(item.url)}">${esc(item.title)}</a></h3>
        <p>${esc(item.description || 'Open this Beaumont Intelligence record.')}</p>
        <a class="text-link" href="${esc(item.url)}">Open result →</a>
      </article>
    `).join('');
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
