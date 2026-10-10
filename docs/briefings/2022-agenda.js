(() => {
  const rows = [...document.querySelectorAll('.agenda-record')];
  const search = document.querySelector('#agenda-search');
  const filter = document.querySelector('#agenda-filter');
  const dialog = document.querySelector('#document-dialog');
  const frame = document.querySelector('#document-frame');
  function render() {
    const term = search.value.trim().toLowerCase();
    rows.forEach(row => {
      row.hidden = (filter.value !== 'all' && filter.value !== row.dataset.section) || !row.textContent.toLowerCase().includes(term);
      if (term && !row.hidden) row.open = true;
    });
    document.querySelectorAll('.agenda-section').forEach(section => { section.hidden = [...section.querySelectorAll('.agenda-record')].every(row => row.hidden); });
    document.querySelector('#agenda-count').textContent = `${rows.filter(row => !row.hidden).length} of ${rows.length} items shown`;
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-document]');
    if (!button) return;
    document.querySelector('#document-title').textContent = button.dataset.title;
    const params = new URLSearchParams({url: button.dataset.document, title: button.dataset.title, returnUrl: location.href, returnLabel: 'Back to interactive agenda'});
    frame.src = '../documents/viewer.html?' + params;
    dialog.showModal();
  });
  document.querySelector('#close-document').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { frame.src = 'about:blank'; });
  search.addEventListener('input', render);
  filter.addEventListener('change', render);
  const target = document.getElementById(location.hash.slice(1));
  if (target?.matches('.agenda-record')) target.open = true;
  render();
})();
