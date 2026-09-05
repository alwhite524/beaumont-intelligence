(() => {
  const records = Array.isArray(window.BI_RESEARCH_LIBRARY) ? window.BI_RESEARCH_LIBRARY : [];
  const search = document.querySelector('#search');
  const topic = document.querySelector('#topic');
  const meeting = document.querySelector('#meeting');
  const topics = document.querySelector('#topics');
  const kit = document.querySelector('.meeting-kit');
  const count = document.querySelector('#count');
  if (!search || !topics) return;

  const meetingLabel = document.querySelector('label[for="meeting"]');
  if (meetingLabel) meetingLabel.textContent = 'Source collection';

  // The meeting filter is a source-collection browser, not a transcript inventory.
  // Dates represented by the curated page are collections; Official City document
  // records identify complete source inventories such as September 1, 2026.
  const curatedDates = [...document.querySelectorAll('#topics .record[data-meeting]')]
    .map(record => record.dataset.meeting)
    .filter(Boolean);
  const indexedCollectionDates = records
    .filter(record => record.type === 'Official City document')
    .map(record => record.date)
    .filter(Boolean);
  const dates = [...new Set([...curatedDates, ...indexedCollectionDates])].sort().reverse();
  meeting.innerHTML = '<option value="all">All source collections</option>' + dates.map(date => {
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
    results.innerHTML = matches.length ? `<section class="topic"><div class="topic-label"><div class="eyebrow">Documents + transcripts</div><h2>Search results</h2><p>Transcript matches can identify meetings even when no source collection has been created.</p></div><div class="collection-list">${matches.map(record => `<article class="record"><div class="record-date"><span>${esc(record.item || record.type)}</span>${esc(record.date || 'Undated')}</div><div><h3>${esc(record.title)}</h3><p>${esc(snippet(record.body, query))}</p></div><div class="links"><span class="doc-count">${esc(record.type)}</span><a href="${esc(record.url)}" target="_blank" rel="noopener">${record.type === 'Meeting transcript' ? 'Open transcript' : 'Open source'} ↗</a></div></article>`).join('')}</div></section>` : '<div class="empty">No indexed document or transcript matches. The City may have additional records not yet cataloged.</div>';
  }
  search.addEventListener('input', render);
  topic.addEventListener('change', () => search.value.trim() && render());
  meeting.addEventListener('change', () => search.value.trim() && render());
})();
