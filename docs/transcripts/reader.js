(async () => {
  const date = new URLSearchParams(location.search).get('date');
  const note = document.querySelector('#transcript-note');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date || '')) { note.textContent = 'Select a meeting from the meeting-source catalog.'; return; }
  try {
    const response = await fetch(`${date}-city-council-transcript.txt`);
    if (!response.ok) throw new Error('Transcript unavailable');
    const text = await response.text();
    const video = text.match(/https:\/\/www\.youtube\.com\/watch\?v=[\w-]+/)?.[0];
    document.querySelector('#transcript-title').textContent = `${date} Council transcript`;
    document.querySelector('#agenda-link').href = `../briefings/${date}-sources.html`;
    document.querySelector('#agenda-link').textContent = 'Back to interactive agenda';
    note.textContent = text.split(/\n(?=\(\d+:)/)[0];
    const rows = [];
    for (const line of text.split('\n')) {
      const match = line.match(/^\((\d+):(\d{2}):(\d{2})\)\s*(.*)$/);
      if (!match) continue;
      const row = document.createElement('div'); row.className = 'transcript-line';
      const link = document.createElement(video ? 'a' : 'span'); link.textContent = `${match[1]}:${match[2]}:${match[3]}`;
      if (video) { link.href = `${video}&t=${Number(match[1])*3600+Number(match[2])*60+Number(match[3])}s`; link.target = '_blank'; link.rel = 'noopener'; }
      const paragraph = document.createElement('p'); paragraph.textContent = match[4];
      row.append(link, paragraph); rows.push(row);
    }
    document.querySelector('#transcript-lines').append(...rows);
    function filter() { const q = document.querySelector('#transcript-search').value.toLowerCase().trim(); rows.forEach(row => row.hidden = !row.textContent.toLowerCase().includes(q)); document.querySelector('#transcript-count').textContent = `${rows.filter(row => !row.hidden).length} of ${rows.length} caption lines`; }
    document.querySelector('#transcript-search').addEventListener('input', filter); filter();
  } catch { note.textContent = 'The transcript could not be loaded. Return to the meeting sources to check availability.'; }
})();
