(() => {
  const supplementalIndex = [{
    title: 'Billboards: Policy and Decisions', url: 'dossiers/billboards.html', category: 'Research Record',
    description: 'Documented history of billboard advertising, regulation, relocation agreements, and digital conversion decisions.',
    text: 'billboards digital signs electronic signs Lamar AMG relocation agreement replacement ratio survey advertising Council history', aliases: ['digital billboard', 'electronic billboard', 'sign policy']
  }, {
    title: 'Downtown Revitalization Intelligence Center',
    url: 'downtown-revitalization.html',
    description: "Follow Beaumont's Elevate 2050 vision, public investment, business programs, mobility questions, design decisions, and Council actions.",
    category: 'Intelligence Center',
    text: 'Downtown Beaumont revitalization Elevate 2050 economic development streetscape Sixth Street Grace Avenue business attraction expansion mixed use pedestrian mobility traffic preliminary engineering Council actions',
    aliases: ['downtown', 'Elevate 2050', 'downtown plan', 'downtown Beaumont']
  }, {
    title: 'Police History', url: 'police-history.html', category: 'Intelligence Center',
    description: 'Verified timeline of Beaumont Police technology, partnership, and facility-planning decisions.',
    text: 'Police history body cameras Intrensic Axon station SRO Peregrine Council actions', aliases: ['police timeline']
  }, {
    title: 'Police Operations and Technology', url: 'police-operations.html', category: 'Intelligence Center',
    description: 'Body-worn cameras, evidence services, investigative search, analytics, and operational technology.',
    text: 'Police operations technology Axon evidence.com Peregrine AI databases analytics drone DFR', aliases: ['police technology']
  }, {
    title: 'Police Staffing and Partnerships', url: 'police-staffing.html', category: 'Intelligence Center',
    description: 'Verified police staffing partnerships and a transparent inventory of workforce evidence gaps.',
    text: 'Police staffing officers vacancies school resource officer SRO BUSD Animal Control', aliases: ['police officers']
  }, {
    title: 'Police Facilities', url: 'police-facilities.html', category: 'Intelligence Center',
    description: "Track Beaumont's future Police Department Station through estimates, priorities, funding, design, and Council actions.",
    text: 'Police station facility Beaumont Avenue Cougar Way CIP estimate design funding construction priority', aliases: ['new police station']
  }, {
    title: 'Police Evidence Explorer', url: 'police-evidence.html', category: 'Intelligence Center',
    description: 'Official videos, meeting records, agreements, policies, and staff reports supporting the Police Intelligence Center.',
    text: 'Police evidence sources contracts transcripts Axon Peregrine SRO station', aliases: ['police sources']
  }, {
    title: 'Downtown Revitalization History', url: 'downtown-revitalization-history.html', category: 'Intelligence Center',
    description: 'Timeline of downtown zoning, Elevate 2050, engineering direction, business incentives, and economic strategy.',
    text: 'downtown history zoning Elevate 2050 engineering incentives strategy', aliases: ['downtown timeline']
  }, {
    title: 'Downtown Plan and Design', url: 'downtown-revitalization-plan.html', category: 'Intelligence Center',
    description: 'Elevate 2050 concepts, proposed design elements, mobility questions, and implementation boundaries.',
    text: 'downtown design Sixth Street Beaumont Avenue Grace Avenue roundabouts walkable mixed use mobility', aliases: ['Elevate 2050 plan']
  }, {
    title: 'Downtown Business Programs', url: 'downtown-revitalization-business.html', category: 'Intelligence Center',
    description: 'Verified downtown business attraction and expansion incentive records.',
    text: 'downtown business grant forgivable loan Cloud9 Cornerstone Tuscano economic development', aliases: ['business incentives']
  }, {
    title: 'Downtown Revitalization Funding', url: 'downtown-revitalization-funding.html', category: 'Intelligence Center',
    description: 'Planning budgets, capital projects, property investment, business incentives, and construction funding.',
    text: 'downtown funding CD03 R25-15 CIP general fund property grants contracts costs', aliases: ['downtown budget']
  }, {
    title: 'Downtown Council Actions', url: 'downtown-revitalization-council-actions.html', category: 'Intelligence Center',
    description: 'Verified Council actions affecting downtown zoning, design, incentives, and economic strategy.',
    text: 'downtown council actions votes zoning engineering Cloud9 Cornerstone Tuscano strategy', aliases: ['downtown decisions']
  }, {
    title: 'Downtown Evidence Explorer', url: 'downtown-revitalization-evidence.html', category: 'Intelligence Center',
    description: 'Primary meeting records, transcripts, plans, staff reports, and agreements supporting the Downtown Center.',
    text: 'downtown evidence sources transcripts plans staff reports agreements', aliases: ['downtown sources']
  }];
  const rawIndex = [
    ...(Array.isArray(window.BI_SEARCH_INDEX) ? window.BI_SEARCH_INDEX : []),
    ...supplementalIndex
  ];
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
