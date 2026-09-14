(() => {
  const search = document.querySelector('#agenda-search');
  const rows = [...document.querySelectorAll('.agenda-record')];
  const dialog = document.querySelector('#viewer-dialog');
  const frame = document.querySelector('#viewer-frame');
  function filter() {
    const term = search.value.trim().toLowerCase();
    rows.forEach(row => { row.hidden = !row.textContent.toLowerCase().includes(term); if (term && !row.hidden) row.open = true; });
    document.querySelectorAll('.agenda-section').forEach(section => { section.hidden = [...section.querySelectorAll('.agenda-record')].every(row => row.hidden); });
    document.querySelector('#agenda-count').textContent = `${rows.filter(row => !row.hidden).length} of ${rows.length} agenda entries shown`;
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-document]');
    if (!button) return;
    const url = new URL(button.dataset.document);
    let fallback = dialog.querySelector('a');
    if (!fallback) { fallback = document.createElement('a'); fallback.textContent = 'Open official record in a new tab'; fallback.target = '_blank'; fallback.rel = 'noopener'; dialog.insertBefore(fallback, frame); }
    fallback.href = url.href;
    frame.src = url.hostname === 'portal.laserfiche.com' ? url.href : `../documents/viewer.html?url=${encodeURIComponent(url.href)}`;
    dialog.showModal();
  });
  document.querySelector('#viewer-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { frame.src = 'about:blank'; });
  function revealHash() {
    const row = document.getElementById(location.hash.slice(1));
    if (row?.matches('.agenda-record')) { search.value = ''; filter(); row.open = true; row.scrollIntoView(); }
  }
  search.addEventListener('input', filter);
  window.addEventListener('hashchange', revealHash);
  filter(); revealHash();
})();
