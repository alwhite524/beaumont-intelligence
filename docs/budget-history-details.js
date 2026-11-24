(() => {
  const year = document.getElementById('budget-detail-year');
  if (!year) return;

  const summaryYear = document.getElementById('budget-year');
  const title = document.getElementById('budget-detail-title');
  const results = document.getElementById('budget-detail-results');
  const status = document.getElementById('budget-detail-status');
  const fiscalYear = value => `FY ${Number(value) - 1}–${value.slice(-2)}`;
  let catalog;

  function showYear() {
    const selected = year.value;
    const label = fiscalYear(selected);
    const { reports, externalSource } = catalog[selected];
    title.textContent = `${label} budget PDFs`;
    results.replaceChildren();
    status.textContent = reports.length === 1
      ? 'The full budget book contains the available fund detail for this year.'
      : reports.length ? '' : 'The City source is available for this year.';
    for (const report of reports) {
      const base = report.source.startsWith('official-documents/')
        ? 'https://documents.beaumontintelligence.com/'
        : location.href;
      const params = new URLSearchParams({
        url: new URL(report.source, base).href,
        title: `${label} ${report.title}`,
        returnUrl: `../budget-annual-history.html?year=${selected}#budget-detail`,
        returnLabel: 'Budget History',
      });
      const link = document.createElement('a');
      link.className = 'btn';
      link.href = 'documents/viewer.html?' + params;
      link.textContent = report.title;
      results.append(link);
    }
    if (externalSource) {
      const link = document.createElement('a');
      link.className = 'text-link';
      link.href = externalSource;
      link.textContent = 'Open City budget source';
      results.append(link);
    }

    const url = new URL(location.href);
    url.searchParams.set('year', selected);
    history.replaceState(null, '', url);
    if (summaryYear.value !== selected && Array.from(summaryYear.options).some(option => option.value === selected)) {
      summaryYear.value = selected;
      summaryYear.dispatchEvent(new Event('change'));
    }
  }

  async function load() {
    year.disabled = true;
    results.replaceChildren();
    status.textContent = 'Loading budget PDFs…';
    try {
      const response = await fetch('budget-details/history-reports.json');
      if (!response.ok) throw new Error('Budget PDF catalog unavailable');
      catalog = await response.json();
      year.replaceChildren(...Object.keys(catalog).reverse().map(value => new Option(fiscalYear(value), value)));
      const requested = new URLSearchParams(location.search).get('year');
      if (Object.hasOwn(catalog, requested)) year.value = requested;
      year.disabled = false;
      showYear();
    } catch {
      status.textContent = 'Budget PDFs could not be loaded.';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'btn';
      retry.textContent = 'Retry';
      retry.addEventListener('click', load);
      results.append(retry);
    }
  }

  year.addEventListener('change', showYear);
  summaryYear.addEventListener('change', () => {
    if (catalog && summaryYear.value !== year.value && Object.hasOwn(catalog, summaryYear.value)) {
      year.value = summaryYear.value;
      showYear();
    }
  });
  load();
})();
