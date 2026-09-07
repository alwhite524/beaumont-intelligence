(() => {
  const records = Array.isArray(window.BI_RESEARCH_LIBRARY) ? window.BI_RESEARCH_LIBRARY : [];
  const search = document.querySelector('#search');
  const topic = document.querySelector('#topic');
  const meeting = document.querySelector('#meeting');
  const modeInputs = [...document.querySelectorAll('input[name="search-mode"]')];
  const topics = document.querySelector('#topics');
  const count = document.querySelector('#count');
  const empty = document.querySelector('#empty');
  if (!search || !topic || !meeting || !topics || !count) return;

  const transcriptType = 'Meeting transcript';
  const documents = records.filter(record => record.type !== transcriptType);
  const staticRows = [...topics.querySelectorAll('.record')];
  const staticGroups = [...topics.querySelectorAll('.topic')];
  const statusCounts = document.querySelectorAll('.library-hero .status span');
  const transcriptCount = records.filter(record => record.type === transcriptType).length;
  if (statusCounts[0]) statusCounts[0].textContent = `${records.length} searchable sources`;
  if (statusCounts[1]) statusCounts[1].textContent = `${transcriptCount} full-text Council transcripts`;

  const transcripts = records.filter(record => record.type === transcriptType);
  const searchMode = () => modeInputs.find(input => input.checked)?.value || 'documents';
  const meetingOptions = sourceRecords => {
    const dates = [...new Set(sourceRecords.map(record => record.date).filter(Boolean))].sort().reverse();
    const allLabel = searchMode() === 'transcripts'
      ? 'All meetings with transcripts'
      : 'All meetings with source documents';
    meeting.innerHTML = `<option value="all">${allLabel}</option>` + dates.map(date => {
    const label = new Date(`${date}T12:00:00`).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    return `<option value="${date}">${label}</option>`;
    }).join('');
  };
  meetingOptions(documents);

  const results = document.createElement('div');
  results.className = 'topic-stack';
  results.hidden = true;
  topics.before(results);

  const esc = value => String(value || '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));
  const norm = value => String(value || '').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
  const compact = value => norm(value).replace(/\s+/g, '');
  const matchesQuery = (value, query) => {
    const searchable = norm(value);
    return searchable.includes(query) || compact(searchable).includes(compact(query));
  };
  const destinationFor = record => record.type === transcriptType
    ? null
    : { href: `viewer.html?url=${encodeURIComponent(record.url)}`, label: 'View document' };
  const secondsFromTimestamp = timestamp => {
    const parts = timestamp.split(':').map(Number);
    if (parts.some(Number.isNaN)) return null;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return null;
  };
  const transcriptHit = (record, query) => {
    if (record.type !== transcriptType) return null;
    let latestTimestamp = null;
    for (const line of String(record.body || '').split(/\r?\n/)) {
      const timestamp = line.match(/^\((\d{1,2}:\d{2}(?::\d{2})?)\)\s*/);
      if (timestamp) latestTimestamp = timestamp;
      if (!matchesQuery(line, query)) continue;
      if (!latestTimestamp) return null;
      const seconds = secondsFromTimestamp(latestTimestamp[1]);
      if (seconds === null) return null;
      return {
        label: latestTimestamp[1],
        seconds,
        text: line.slice(timestamp ? timestamp[0].length : 0),
      };
    }
    return null;
  };
  const watchUrl = (videoUrl, seconds) => {
    try {
      const url = new URL(videoUrl);
      url.searchParams.set('t', `${seconds}s`);
      return url.toString();
    } catch {
      return '';
    }
  };
  const snippet = (body, query) => {
    const text = String(body || '').replace(/\s+/g, ' ').trim();
    if (!query) return text.slice(0, 210);
    const lowered = text.toLowerCase();
    const positions = query.split(' ').filter(Boolean)
      .map(word => lowered.indexOf(word)).filter(index => index >= 0);
    const at = positions.length ? Math.min(...positions) : 0;
    return `${at > 70 ? '…' : ''}${text.slice(Math.max(0, at - 70), at + query.length + 140)}${at + query.length + 140 < text.length ? '…' : ''}`;
  };
  const recordMatchesFilters = record =>
    (topic.value === 'all' || record.topic === topic.value) &&
    (meeting.value === 'all' || record.date === meeting.value);

  const showCollections = () => {
    results.hidden = true;
    topics.hidden = false;
    staticRows.forEach(row => { row.hidden = false; });
    staticGroups.forEach(group => { group.hidden = false; });
    count.textContent = `Showing ${staticRows.length} source ${staticRows.length === 1 ? 'collection' : 'collections'} across ${staticGroups.length} civic ${staticGroups.length === 1 ? 'topic' : 'topics'}`;
    if (empty) empty.hidden = staticRows.length !== 0;
  };

  const renderRecords = (matches, query, mode) => {
    topics.hidden = true;
    results.hidden = false;
    if (empty) empty.hidden = true;
    const transcriptMode = mode === 'transcripts';
    count.textContent = transcriptMode
      ? `Showing ${matches.length} matching meeting ${matches.length === 1 ? 'transcript' : 'transcripts'}`
      : `Showing ${matches.length} source ${matches.length === 1 ? 'document' : 'documents'}`;
    const heading = transcriptMode ? 'Transcript results' : 'Source documents';
    const eyebrow = transcriptMode ? 'Council transcripts' : 'Official records';
    const explanation = transcriptMode
      ? 'Transcript matches identify the meeting and link directly to the matching moment in the video.'
      : 'Every indexed source document matching the selected topic and meeting is shown below.';
    results.innerHTML = matches.length ? `<section class="topic"><div class="topic-label"><div class="eyebrow">${eyebrow}</div><h2>${heading}</h2><p>${explanation}</p></div><div class="collection-list">${matches.map(record => {
      const hit = query ? transcriptHit(record, query) : null;
      const resultSnippet = hit ? hit.text : snippet(record.body, query);
      const videoLink = hit && record.videoUrl ? watchUrl(record.videoUrl, hit.seconds) : '';
      const watchLink = videoLink
        ? `<a href="${esc(videoLink)}" target="_blank" rel="noopener">Watch video at ${esc(hit.label)} ↗</a>`
        : '';
      const destination = destinationFor(record);
      const destinationLink = destination
        ? `<a href="${esc(destination.href)}" data-library-route="true">${esc(destination.label)} →</a>`
        : '';
      return `<article class="record"><div class="record-date"><span>${esc(record.item || record.type)}</span>${esc(record.date || 'Undated')}</div><div><h3>${esc(record.title)}</h3><p>${esc(resultSnippet)}</p></div><div class="links"><span class="doc-count">${esc(record.type)}</span>${watchLink}${destinationLink}</div></article>`;
    }).join('')}</div></section>` : `<div class="empty">${transcriptMode ? 'No transcript matches that word or phrase.' : 'No source documents match those filters.'}</div>`;
  };

  function render() {
    const mode = searchMode();
    const query = norm(search.value.trim());
    if (mode === 'documents' && !query && topic.value === 'all' && meeting.value === 'all') {
      showCollections();
      return;
    }
    if (mode === 'transcripts' && !query) {
      topics.hidden = true;
      results.hidden = false;
      if (empty) empty.hidden = true;
      count.textContent = 'Enter a word or phrase to search the collected Council transcripts.';
      results.innerHTML = '<div class="empty">Search transcript text to find matching meetings and jump directly to the relevant video timestamp.</div>';
      return;
    }
    const sourceRecords = mode === 'transcripts' ? transcripts : documents;
    const matches = sourceRecords.filter(record => {
      if (!recordMatchesFilters(record)) return false;
      if (mode === 'transcripts') return Boolean(transcriptHit(record, query));
      return !query || matchesQuery(`${record.title} ${record.item} ${record.body}`, query);
    }).slice(0, 100);
    renderRecords(matches, query, mode);
  }

  search.addEventListener('input', render);
  topic.addEventListener('change', render);
  meeting.addEventListener('change', render);
  modeInputs.forEach(input => input.addEventListener('change', () => {
    const transcriptMode = searchMode() === 'transcripts';
    topic.value = 'all';
    topic.disabled = transcriptMode;
    meetingOptions(transcriptMode ? transcripts : documents);
    search.placeholder = transcriptMode
      ? 'Try “billboard,” “Brookside,” or “short-term rental”…'
      : 'Try “budget,” “Pennsylvania,” or “J.2”…';
    render();
  }));

  // All indexed documents use the Library viewer. Transcript text stays local,
  // while timestamp buttons open the corresponding moment on YouTube.
  document.querySelectorAll('a[href^="https://documents.beaumontintelligence.com/"], a[href^="https://pub-beaumont.escribemeetings.com/"]').forEach(link => {
    link.href = `viewer.html?url=${encodeURIComponent(link.href)}`;
    link.dataset.libraryRoute = 'true';
    link.removeAttribute('target');
  });
  document.addEventListener('click', event => {
    if (event.target.closest('[data-library-route="true"]')) event.stopImmediatePropagation();
  }, true);
  render();
})();
