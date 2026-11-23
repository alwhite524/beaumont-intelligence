(() => {
  const byId = id => document.getElementById(id);
  const cityArchive = 'https://documents.beaumontintelligence.com/official-documents/';
  const budgetSources = [
    {
      year: 2023,
      source: 'https://mccmeetings.blob.core.usgovcloudapi.net/beaumntca-pubu/MEET-Packet-ada51768922143e7aa781ac02b57d63d.pdf#page=150',
      funds: { 'General Fund': [60668702, 53291770], Wastewater: [12858001, 14495213], Transit: [2771617, 2771617] }
    },
    {
      year: 2024,
      source: 'https://www.beaumontca.gov/DocumentCenter/View/40164/2024-Cleargov-budget-book-printed-version-61623?bidId=',
      funds: { 'General Fund': [67789803, 67789803], Wastewater: [13422801, 13603377], Transit: [3316669, 2993669] }
    },
    {
      year: 2025,
      source: 'https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId=4367',
      funds: { 'General Fund': [68117655, 66734916], Wastewater: [14830049, 14830049], Transit: [3278071, 3278071] }
    },
    {
      year: 2026,
      source: 'https://www.beaumontca.gov/DocumentCenter/View/39925/FY2026-Budget-In-Brief?bidId=',
      funds: { 'General Fund': [72401809, 72110000] },
      rounded: true
    },
    {
      year: 2027,
      source: cityArchive + '2026-06-16/i-1-staff-report-fy27-budget-gann-and-cip-adoption.pdf',
      funds: { 'General Fund': [75562383, 75562383], Wastewater: [16781283, 16781283], Transit: [3908744, 3908744] }
    }
  ];
  const currency = new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0
  });
  const compact = new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 2
  });
  const percent = new Intl.NumberFormat('en-US', {
    style: 'percent', maximumFractionDigits: 1, signDisplay: 'exceptZero'
  });
  const fy = year => `FY ${year - 1}–${String(year).slice(-2)}`;
  const signed = (value, formatter) => (value > 0 ? '+' : '') + formatter.format(value);
  const element = (tag, content, className) => {
    const node = document.createElement(tag);
    if (content !== undefined) node.textContent = content;
    if (className) node.className = className;
    return node;
  };
  const link = (label, href) => {
    const anchor = element('a', label);
    anchor.href = href;
    return anchor;
  };
  const options = (select, values, emptyLabel) => {
    const items = values.map(([value, label]) => new Option(label, value));
    if (emptyLabel) items.unshift(new Option(emptyLabel, ''));
    select.replaceChildren(...items);
  };

  if (byId("budget-fund")) {
    const fund = byId('budget-fund');
    const year = byId('budget-year');
    const baseline = byId('budget-baseline');
    const metrics = ['Revenue', 'Expenditures', 'Revenue less expenditures'];
    const values = record => {
      const [revenue, expenditures] = record.funds[fund.value];
      return [revenue, expenditures, revenue - expenditures];
    };
    const available = () => budgetSources.filter(record => record.funds[fund.value]);

    function renderBudget() {
      const records = available();
      const current = records.find(record => record.year === Number(year.value));
      const prior = records.find(record => record.year === Number(baseline.value));
      const currentValues = values(current);
      const priorValues = values(prior);
      const approximate = (record, index) => record.rounded && index > 0 ? '≈' : '';
      const change = (index, formatter) => {
        const prefix = approximate(current, index) || approximate(prior, index);
        return prefix + signed(currentValues[index] - priorValues[index], formatter);
      };

      byId('budget-kpis').replaceChildren(...metrics.map((metric, index) => {
        const card = element('article', undefined, 'finance-kpi');
        const delta = priorValues[index] > 0
          ? ` (${percent.format((currentValues[index] - priorValues[index]) / priorValues[index])})`
          : '';
        card.append(element('h3', metric), element('strong', approximate(current, index) + compact.format(currentValues[index])),
          element('p', `${change(index, compact)}${index < 2 ? delta : ''} vs. ${fy(prior.year)}`));
        return card;
      }));

      const max = Math.max(...records.flatMap(record => values(record).slice(0, 2)));
      byId('budget-chart').replaceChildren(...budgetSources.map(record => {
        const row = element('div', undefined, 'finance-chart-row');
        row.classList.toggle('finance-chart-selected', record === current);
        row.append(element('strong', fy(record.year)));
        if (!record.funds[fund.value]) {
          row.append(element('span', 'Figures unavailable', 'finance-note'));
          return row;
        }
        const bars = element('div');
        values(record).slice(0, 2).forEach((amount, index) => {
          const bar = element('div', undefined, 'finance-bar');
          const meter = element('meter');
          meter.min = 0;
          meter.max = max;
          meter.value = amount;
          const label = approximate(record, index) + currency.format(amount);
          meter.setAttribute('aria-label', `${fy(record.year)} ${metrics[index]} ${label}`);
          bar.append(meter, element('span', approximate(record, index) + compact.format(amount)));
          bars.append(bar);
        });
        row.append(bars);
        return row;
      }));

      const table = element('table', undefined, 'finance-table');
      table.setAttribute('aria-labelledby', 'comparison-title');
      const headings = table.createTHead().insertRow();
      headings.append(element('th', 'Metric'), element('th'), element('th'), element('th', 'Change'));
      headings.cells[1].append(link(fy(prior.year), prior.source));
      headings.cells[2].append(link(fy(current.year), current.source));
      const body = table.createTBody();
      metrics.forEach((metric, index) => {
        const row = body.insertRow();
        const heading = element('th', metric);
        heading.scope = 'row';
        row.append(heading);
        row.insertCell().textContent = approximate(prior, index) + currency.format(priorValues[index]);
        row.insertCell().textContent = approximate(current, index) + currency.format(currentValues[index]);
        row.insertCell().textContent = change(index, currency);
      });
      byId('budget-table').replaceChildren(table);
      byId('budget-coverage').textContent =
        'Years use the City’s published operating fund totals, including transfers where reported. ≈ indicates a calculation or display based on the rounded FY 2025–26 expenditure figure.';
    }

    function updateBaseline() {
      const candidates = available().filter(record => record.year !== Number(year.value));
      options(baseline, candidates.map(record => [record.year, fy(record.year)]));
      const previous = candidates.filter(record => record.year < Number(year.value)).at(-1);
      baseline.value = (previous || candidates[0]).year;
      renderBudget();
    }

    function updateFund() {
      const preferred = Number(year.value);
      const records = available();
      options(year, records.map(record => [record.year, fy(record.year)]));
      year.value = records.some(record => record.year === preferred) ? preferred : records.at(-1).year;
      updateBaseline();
    }

    fund.addEventListener('change', updateFund);
    year.addEventListener('change', () => updateBaseline());
    baseline.addEventListener('change', renderBudget);
    updateFund();

  }

  if (!byId("capital-results")) return;

  const plans = window.beaumontCapitalPlans.slice(-1).map(plan => ({
    ...plan,
    projects: plan.projects.map(([id, name, department, type, cost, funding, gap, page]) => ({
      id, name, department, type, cost, funding, gap, page
    }))
  }));
  const department = byId('capital-department');
  const direction = byId('capital-direction');
  let descending = true;
  const search = byId('capital-search');
  const type = byId('capital-type');
  const status = byId('capital-status');
  const sort = byId('capital-sort');
  const results = byId('capital-results');
  const more = byId('capital-more');
  const pageSize = 12;
  let visible = pageSize;
  const departments = {
    PW: 'Public Works', COMDV: 'Community Development', COMSRV: 'Community Services',
    FIRE: 'Fire', IT: 'Information Technology', PD: 'Police', WW: 'Wastewater', TRANSIT: 'Transit'
  };
  options(department, [...new Set(plans[0].projects.map(p=>p.department))].sort().map(value=>[value, departments[value] || value]), 'All departments');
  const types = [...new Set(plans.flatMap(plan => plan.projects.map(project => project.type)))].sort();
  options(type, types.map(value => [value, value]), 'All types');

  function renderCapital() {
    const plan = plans[0];
    byId('capital-source').href = plan.source;
    const term = search.value.trim().toLowerCase();
    const statuses = {
      '': () => true,
      gap: project => project.gap > 0,
      funded: project => project.cost > 0 && project.gap === 0,
      unpriced: project => project.cost === 0
    };
    const order = sort.value;
    const matches = plan.projects
      .filter(project => `${project.id} ${project.name} ${project.type} ${departments[project.department] || project.department}`.toLowerCase().includes(term))
      .filter(project => !type.value || project.type === type.value)
      .filter(project => !department.value || project.department === department.value)
      .filter(statuses[status.value])
      .sort((a, b) => (descending ? -1 : 1) * (typeof a[order] === 'number' ? a[order]-b[order] : a[order].localeCompare(b[order], undefined, {numeric:true})) || a.name.localeCompare(b.name));
    direction.textContent = descending ? 'Descending' : 'Ascending';
    direction.setAttribute('aria-label', `Sort direction: ${descending?'descending':'ascending'}. Change direction`);

    byId('capital-count').textContent = matches.length
      ? `Showing ${Math.min(visible, matches.length)} of ${matches.length} ${matches.length === 1 ? 'project' : 'projects'}`
      : 'No projects match these filters.';
    more.hidden = matches.length <= visible;
    const table = element('table', undefined, 'finance-table capital-table');
    table.setAttribute('aria-labelledby', 'capital-title');
    const header = table.createTHead().insertRow();
    const fields = ['Project', 'Estimated cost', 'Programmed funding', 'Unfunded'];
    header.append(...fields.map((field, i) => {const th=element('th');th.scope='col';const key=['name','cost','funding','gap'][i];th.setAttribute('aria-sort',order===key?(descending?'descending':'ascending'):'none');const button=element('button',field+(order===key?(descending?' ▼':' ▲'):''));button.type='button';button.addEventListener('click',()=>{descending=sort.value===key?!descending:false;sort.value=key;visible=pageSize;renderCapital();});th.append(button);return th;}));
    const body = table.createTBody();
    for (const project of matches.slice(0, visible)) {
      const row = body.insertRow();
      const heading = element('th');
      heading.scope = 'row';
      heading.append(link(project.name, `${plan.source}#page=${project.page}`),
        element('small', `${project.id} · ${project.type} · ${departments[project.department] || project.department}`));
      row.append(heading);
      [project.cost, project.funding, project.gap].forEach((value, index) => {
        const cell = row.insertCell();
        cell.append(element('span', fields[index + 1], 'capital-mobile-label'),
          element('span', project.cost === 0 ? '—' : currency.format(value)));
      });
    }
    results.replaceChildren(...(matches.length ? [table] : []));
  }

  for (const control of [department, type, status, sort, search]) {
    control.addEventListener(control === search ? 'input' : 'change', () => {
      visible = pageSize;
      renderCapital();
    });
  }
  direction.addEventListener('click',()=>{descending=!descending;visible=pageSize;renderCapital();});
  more.addEventListener('click', () => {
    visible += pageSize;
    renderCapital();
    const firstNewLink = results.querySelectorAll('tbody a')[visible - pageSize];
    firstNewLink?.focus();
  });
  renderCapital();
})();
