(() => {
  const year = document.getElementById('budget-detail-year');
  if (!year) return;

  const summaryYear = document.getElementById('budget-year');
  const title = document.getElementById('budget-detail-title');
  const results = document.getElementById('budget-detail-results');
  const comparisonPanel = document.getElementById('budget-detail-comparison');
  const status = document.getElementById('budget-detail-status');
  const fiscalYear = value => `FY ${Number(value) - 1}–${value.slice(-2)}`;
  const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  const change = amount => (amount > 0 ? '+' : '') + money.format(amount);
  let catalog;

  function comparisonTable(caption, labels, rows) {
    const table = document.createElement('table');
    table.className = 'finance-table';
    table.createCaption().textContent = caption;
    const heading = table.createTHead().insertRow();
    for (const label of ['Fund and category', ...labels]) {
      const cell = document.createElement('th');
      cell.scope = 'col';
      cell.textContent = label;
      heading.append(cell);
    }
    const body = table.createTBody();
    for (const [label, ...values] of rows) {
      const tr = body.insertRow();
      const name = document.createElement('th');
      name.scope = 'row';
      name.textContent = label;
      tr.append(name);
      values.forEach((value, index) => {
        const cell = tr.insertCell();
        cell.dataset.label = labels[index];
        cell.textContent = value;
      });
    }
    return table;
  }

  function showComparison(comparison) {
    comparisonPanel.replaceChildren();
    if (!comparison) return;
    const hasActuals = comparison.rows.every(row => Number.isFinite(row.actual));
    const labels = ['Original budget', comparison.latestLabel, 'Budget change'];
    if (hasActuals) labels.push('Reported actual', 'Actual − final');
    const rows = comparison.rows.map(row => {
      const values = [row.label, money.format(row.original), money.format(row.latest), change(row.latest - row.original)];
      if (hasActuals) values.push(money.format(row.actual), change(row.actual - row.latest));
      return values;
    });
    comparisonPanel.append(comparisonTable('Original and revised budget totals', labels, rows));
    if (!hasActuals || !['2024', '2025'].includes(year.value)) return;

    const prior = catalog['2024'].comparison.rows;
    const recent = catalog['2025'].comparison.rows;
    const trend = recent.map(row => {
      const earlier = prior.find(item => item.label === row.label);
      return [row.label, money.format(earlier.actual), money.format(row.actual), change(row.actual - earlier.actual)];
    });
    comparisonPanel.append(comparisonTable('General Fund actuals year over year',
      ['FY 2023–24 actual', 'FY 2024–25 actual', 'Year-over-year change'], trend));
  }

  function showYear() {
    const selected = year.value;
    const label = fiscalYear(selected);
    const { reports, externalSource, comparison, note } = catalog[selected];
    title.textContent = `${label} budget records`;
    results.replaceChildren();
    showComparison(comparison);
    status.textContent = comparison?.note || note || (reports.length === 1
      ? 'The full budget book contains the available fund detail for this year.'
      : reports.length ? '' : 'The City source is available for this year.');
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
      if (report.page) params.set('page', report.page);
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
      const response = await fetch('budget-details/history-reports.json?v=20261124-two-year-pilot');
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
