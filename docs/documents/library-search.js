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
  const minutes = records.filter(record => record.type === 'Meeting minutes');
  const documents = records.filter(record => record.type !== transcriptType && record.type !== 'Meeting minutes');
  const staticRows = [...topics.querySelectorAll('.record')];
  const staticGroups = [...topics.querySelectorAll('.topic')];
  const statusCounts = document.querySelectorAll('.library-hero .status span');
  const transcriptCount = records.filter(record => record.type === transcriptType).length;
  if (statusCounts[0]) statusCounts[0].textContent = `${records.length} searchable sources`;
  if (statusCounts[1]) statusCounts[1].textContent = `${transcriptCount} full-text Council transcripts`;

  const transcripts = records.filter(record => record.type === transcriptType);
  const searchMode = () => modeInputs.find(input => input.checked)?.value || 'all';
  const meetingOptions = sourceRecords => {
    const dates = [...new Set(sourceRecords.map(record => record.date).filter(Boolean))].sort().reverse();
    const allLabel = searchMode() === 'transcripts'
      ? 'All meetings with transcripts'
      : searchMode() === 'minutes' ? 'All available minutes' : 'All meetings';
    meeting.innerHTML = `<option value="all">${allLabel}</option>` + dates.map(date => {
    const label = new Date(`${date}T12:00:00`).toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    return `<option value="${date}">${label}</option>`;
    }).join('');
  };
  meetingOptions(searchMode() === 'all' ? records : documents);

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
    ? { href: record.url, label: 'Read transcript' }
    : record.type === 'Agenda item' || record.type === 'Council evidence summary'
    ? { href: record.url, label: record.type === 'Agenda item' ? 'Open agenda item' : 'Read evidence summary' }
    : /\.docx$/i.test(record.url)
    ? { href: record.url, label: 'Download Word original' }
    : record.url.startsWith('https://portal.laserfiche.com/')
    ? { href: record.url, label: 'Open official archive' }
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
    const segments = [];
    let latestTimestamp = null;
    for (const line of String(record.body || '').split(/\r?\n/)) {
      const timestamp = line.match(/^\((\d{1,2}:\d{2}(?::\d{2})?)\)\s*/);
      if (timestamp) latestTimestamp = timestamp;
      if (!latestTimestamp) continue;
      const seconds = secondsFromTimestamp(latestTimestamp[1]);
      if (seconds === null) continue;
      const text = line.slice(timestamp ? timestamp[0].length : 0).trim();
      if (!text) continue;
      segments.push({
        label: latestTimestamp[1],
        seconds,
        text,
      });
    }
    // Captions can divide one spoken phrase across several timestamped lines.
    for (const compactMode of [false, true]) {
      const normalize = compactMode ? compact : norm;
      const separator = compactMode ? '' : ' ';
      const parts = segments.map(segment => normalize(segment.text));
      const needle = normalize(query);
      const at = parts.join(separator).indexOf(needle);
      if (!needle || at < 0) continue;
      let offset = 0;
      const first = parts.findIndex(part => {
        const end = offset + part.length;
        if (at < end) return true;
        offset = end + separator.length;
        return false;
      });
      if (first < 0) continue;
      let end = first;
      let covered = offset + parts[first].length;
      while (covered < at + needle.length && end + 1 < parts.length) {
        covered += separator.length + parts[++end].length;
      }
      return { ...segments[first], text: segments.slice(first, end + 1).map(segment => segment.text).join(' ') };
    }
    return null;
  };
  const minuteHits = (record, query) => {
    if (!query || !record.annualCompilation || !Array.isArray(record.textPages)) return [];
    return record.textPages.flatMap((pageText, index) => matchesQuery(pageText, query) ? [{
      page: index + 1,
      date: record.pageDates?.[index] || '',
      text: snippet(pageText, query),
    }] : []);
  };
  const formatMeetingDate = value => value ? new Date(`${value}T12:00:00`).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  }) : 'Meeting date not identified';
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
    const minutesMode = mode === 'minutes';
    count.textContent = transcriptMode
      ? `Showing ${matches.length} matching meeting ${matches.length === 1 ? 'transcript' : 'transcripts'}`
      : minutesMode ? `Showing ${matches.length} minutes records` : `Showing ${matches.length} source ${matches.length === 1 ? 'document' : 'documents'}`;
    const heading = mode === 'all' ? 'All source results' : transcriptMode ? 'Transcript results' : mode === 'minutes' ? 'Council minutes' : 'Source documents';
    const eyebrow = transcriptMode ? 'Council transcripts' : 'Official records';
    const explanation = transcriptMode
      ? 'Transcript matches identify the meeting and link directly to the matching moment in the video.'
      : mode === 'minutes' ? 'Searchable text comes from PDF and Word minutes and may contain extraction errors or omissions. Open the original to verify a result. Word originals download rather than opening in the PDF viewer. Annual compilations are listed separately from individual meeting dates.' : 'Every indexed source document matching the selected topic and meeting is shown below.';
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
      const annualHits = record.type === 'Meeting minutes' ? minuteHits(record, query) : [];
      const annualHitLinks = annualHits.length ? `<div class="minute-page-hits"><strong>${annualHits.length} matching ${annualHits.length === 1 ? 'page' : 'pages'}:</strong>${annualHits.map(pageHit => {
        const href = `viewer.html?url=${encodeURIComponent(record.url)}&title=${encodeURIComponent(record.title)}&page=${pageHit.page}`;
        return `<div><a href="${esc(href)}" data-library-route="true">${esc(formatMeetingDate(pageHit.date))} — PDF page ${pageHit.page} →</a><p>${esc(pageHit.text)}</p></div>`;
      }).join('')}</div>` : '';
      return `<article class="record"><div class="record-date"><span>${esc(record.item || record.type)}</span>${esc(record.date || 'Annual compilation')}</div><div><h3>${esc(record.title)}</h3><p>${esc(resultSnippet)}</p>${annualHitLinks}</div><div class="links"><span class="doc-count">${esc(record.type)}</span>${watchLink}${destinationLink}</div></article>`;
    }).join('')}</div></section>` : `<div class="empty">${transcriptMode ? 'No transcript matches that word or phrase.' : minutesMode ? 'No minutes match those filters.' : 'No source documents match those filters.'}</div>`;
  };

  function render() {
    const mode = searchMode();
    const query = norm(search.value.trim());
    if ((mode === 'documents' || mode === 'all') && !query && topic.value === 'all' && meeting.value === 'all') {
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
    const sourceRecords = mode === 'all' ? records : mode === 'transcripts' ? transcripts : mode === 'minutes' ? minutes : documents;
    const matches = sourceRecords.filter(record => {
      if (!recordMatchesFilters(record)) return false;
      if (record.type === transcriptType) return !query || Boolean(transcriptHit(record, query));
      return !query || matchesQuery(`${record.title} ${record.item} ${record.body}`, query);
    });
    renderRecords(matches, query, mode);
  }

  search.addEventListener('input', render);
  topic.addEventListener('change', render);
  meeting.addEventListener('change', render);
  modeInputs.forEach(input => input.addEventListener('change', () => {
    const transcriptMode = searchMode() === 'transcripts';
    topic.value = 'all';
    topic.disabled = !['documents', 'all'].includes(searchMode());
    meetingOptions(searchMode() === 'all' ? records : transcriptMode ? transcripts : searchMode() === 'minutes' ? minutes : documents);
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
