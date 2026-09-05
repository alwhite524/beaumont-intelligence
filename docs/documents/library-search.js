(() => {
  const records = Array.isArray(window.BI_RESEARCH_LIBRARY) ? window.BI_RESEARCH_LIBRARY : [];
  const search = document.querySelector('#search');
  const topic = document.querySelector('#topic');
  const meeting = document.querySelector('#meeting');
  const topics = document.querySelector('#topics');
  const kit = document.querySelector('.meeting-kit');
  const count = document.querySelector('#count');
  if (!search || !topics) return;

  const statusCounts = document.querySelectorAll('.library-hero .status span');
  const transcriptCount = records.filter(record => record.type === 'Meeting transcript').length;
  if (statusCounts[0]) statusCounts[0].textContent = `${records.length} searchable sources`;
  if (statusCounts[1]) statusCounts[1].textContent = `${transcriptCount} full-text Council transcripts`;

  const meetingLabel = document.querySelector('label[for="meeting"]');
  if (meetingLabel) meetingLabel.textContent = 'Council meeting';

  // Include every meeting represented by searchable Library material. Records
  // without a meeting date remain searchable but do not create an empty option.
  const dates = [...new Set(records
    .map(record => record.date)
    .filter(Boolean))].sort().reverse();
  meeting.innerHTML = '<option value="all">All meetings with sources</option>' + dates.map(date => {
    const label = new Date(`${date}T12:00:00`).toLocaleDateString('en-US', {year:'numeric', month:'long', day:'numeric'});
    return `<option value="${date}">${label}</option>`;
  }).join('');

  const results = document.createElement('div');
  results.className = 'topic-stack';
  results.hidden = true;
  topics.before(results);
  const esc = value => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const norm = value => String(value || '').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
  const compact = value => norm(value).replace(/\s+/g, '');
  const matchesQuery = (value, query) => {
    const searchable = norm(value);
    return searchable.includes(query) || compact(searchable).includes(compact(query));
  };
  const documentDestination = record => {
    const viewableDocument = /^(Archived document|Official City document)$/.test(record.type) &&
      /^https:\/\/(documents\.beaumontintelligence\.com|pub-beaumont\.escribemeetings\.com)\//i.test(record.url);
    if (viewableDocument) {
      return {
        href: `viewer.html?url=${encodeURIComponent(record.url)}`,
        label: 'View document',
        external: false,
      };
    }
    return {
      href: record.url,
      label: record.type === 'Meeting transcript' ? 'Open transcript' : 'Open original source',
      external: record.type !== 'Meeting transcript',
    };
  };
  const secondsFromTimestamp = timestamp => {
    const parts = timestamp.split(':').map(Number);
    if (parts.some(Number.isNaN)) return null;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return null;
  };
  const transcriptHit = (record, query) => {
    if (record.type !== 'Meeting transcript') return null;
    const line = String(record.body || '').split(/\r?\n/).find(value => matchesQuery(value, query));
    if (!line) return null;
    const match = line.match(/^\((\d{1,2}:\d{2}(?::\d{2})?)\)\s*/);
    if (!match) return null;
    const seconds = secondsFromTimestamp(match[1]);
    return seconds === null ? null : { label: match[1], seconds, text: line.slice(match[0].length) };
  };
  const snippet = (body, query) => {
    const text = String(body || '').replace(/\s+/g, ' ').trim();
    const normalized = norm(text);
    let at = normalized.indexOf(query);
    if (at < 0) at = normalized.indexOf(compact(query));
    if (at < 0) return text.slice(0, 210);
    return `${at > 70 ? '…' : ''}${text.slice(Math.max(0, at - 70), at + query.length + 140)}${at + query.length + 140 < text.length ? '…' : ''}`;
  };

  function render() {
    const query = norm(search.value.trim());
    if (!query) {
      results.hidden = true;
      topics.hidden = false;
      kit.hidden = false;
      return;
    }
    const matches = records.filter(record =>
      matchesQuery(`${record.title} ${record.item} ${record.body}`, query) &&
      (topic.value === 'all' || record.topic === topic.value) &&
      (meeting.value === 'all' || record.date === meeting.value)
    ).slice(0, 100);
    topics.hidden = true;
    kit.hidden = true;
    results.hidden = false;
    const transcriptMatches = matches.filter(record => record.type === 'Meeting transcript').length;
    count.textContent = `Showing ${matches.length} matching records, including ${transcriptMatches} meeting ${transcriptMatches === 1 ? 'transcript' : 'transcripts'}`;
    results.innerHTML = matches.length ? `<section class="topic"><div class="topic-label"><div class="eyebrow">Documents + transcripts</div><h2>Search results</h2><p>Transcript matches can identify meetings even when no source collection has been created.</p></div><div class="collection-list">${matches.map(record => {
      const hit = transcriptHit(record, query);
      const resultSnippet = hit ? hit.text : snippet(record.body, query);
      const watchLink = hit && record.videoUrl
        ? `<a href="${esc(record.videoUrl)}&amp;t=${hit.seconds}s" target="_blank" rel="noopener">Watch at ${esc(hit.label)} ↗</a>`
        : '';
      const destination = documentDestination(record);
      return `<article class="record"><div class="record-date"><span>${esc(record.item || record.type)}</span>${esc(record.date || 'Undated')}</div><div><h3>${esc(record.title)}</h3><p>${esc(resultSnippet)}</p></div><div class="links"><span class="doc-count">${esc(record.type)}</span>${watchLink}<a href="${esc(destination.href)}" data-library-route="true"${destination.external ? ' data-open-external="true" target="_blank" rel="noopener"' : ''}>${esc(destination.label)} ${destination.external ? '↗' : '→'}</a></div></article>`;
    }).join('')}</div></section>` : '<div class="empty">No indexed document or transcript matches. The City may have additional records not yet cataloged.</div>';
  }
  search.addEventListener('input', render);
  topic.addEventListener('change', () => search.value.trim() && render());
  meeting.addEventListener('change', () => search.value.trim() && render());

  // Route trusted archived and City-hosted PDFs through the full Library viewer.
  document.querySelectorAll('a[href^="https://documents.beaumontintelligence.com/"], a[href^="https://pub-beaumont.escribemeetings.com/"]').forEach(link => {
    link.href = `viewer.html?url=${encodeURIComponent(link.href)}`;
    link.dataset.libraryRoute = 'true';
    link.removeAttribute('target');
  });
  document.addEventListener('click', event => {
    if (event.target.closest('[data-library-route="true"]')) event.stopImmediatePropagation();
  }, true);
})();
