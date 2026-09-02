(() => {
  const records = Array.isArray(window.BI_RESEARCH_LIBRARY) ? window.BI_RESEARCH_LIBRARY : [];
  const search = document.querySelector('#search');
  const topic = document.querySelector('#topic');
  const meeting = document.querySelector('#meeting');
  const topics = document.querySelector('#topics');
  const kit = document.querySelector('.meeting-kit');
  const count = document.querySelector('#count');
  if (!search || !topics) return;

  const dates = [...new Set(records.map(record => record.date).filter(Boolean))].sort().reverse();
  meeting.innerHTML = '<option value="all">All meeting dates</option>' + dates.map(date => {
    const label = new Date(`${date}T12:00:00`).toLocaleDateString('en-US', {year:'numeric', month:'long', day:'numeric'});
    return `<option value="${date}">${label}</option>`;
  }).join('');

  const results = document.createElement('div');
  results.className = 'topic-stack';
  results.hidden = true;
  topics.before(results);
  const esc = value => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const norm = value => String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const snippet = (body, query) => {
    const text = String(body || '').replace(/\s+/g, ' ').trim();
    const at = norm(text).indexOf(query);
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
      norm(`${record.title} ${record.item} ${record.body}`).includes(query) &&
      (topic.value === 'all' || record.topic === topic.value) &&
      (meeting.value === 'all' || record.date === meeting.value)
    ).slice(0, 100);
    topics.hidden = true;
    kit.hidden = true;
    results.hidden = false;
    count.textContent = `Showing ${matches.length} matching records from ${records.length} searchable documents and transcripts`;
    results.innerHTML = matches.length ? `<section class="topic"><div class="topic-label"><div class="eyebrow">All sources</div><h2>Search results</h2><p>Archived copies, City-hosted records, and transcript text.</p></div><div class="collection-list">${matches.map(record => `<article class="record"><div class="record-date"><span>${esc(record.item || record.type)}</span>${esc(record.date || 'Undated')}</div><div><h3>${esc(record.title)}</h3><p>${esc(snippet(record.body, query))}</p></div><div class="links"><span class="doc-count">${esc(record.type)}</span><a href="${esc(record.url)}" target="_blank" rel="noopener">Open source ↗</a></div></article>`).join('')}</div></section>` : '<div class="empty">No indexed records match. The City may have additional records not yet cataloged.</div>';
  }
  search.addEventListener('input', render);
  topic.addEventListener('change', () => search.value.trim() && render());
  meeting.addEventListener('change', () => search.value.trim() && render());
})();
