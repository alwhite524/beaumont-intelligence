(() => {
  const configs = {
    'stewart-park': { percent: 95, level: 'Advanced', tasks: ['Add final construction closeout and acceptance records as phases finish.', 'Reconcile current project accounting, grant reimbursements, and remaining balances.', 'Publish final completion evidence and post-construction outcomes.'] },
    'animal-control': { percent: 80, level: 'Strong', tasks: ['Add current service-volume, response-time, sheltering, and outcome trends.', 'Track municipal-shelter design, construction cost, operating plan, and transition milestones.', 'Complete multi-year staffing, contract-performance, complaint, and enforcement records.'] },
    'potrero': { percent: 85, level: 'Strong', tasks: ['Verify the current delivery and construction schedule through primary records.', 'Reconcile grants, local contributions, contracts, amendments, expenditures, and remaining need.', 'Add construction milestones, traffic impacts, change orders, and completion evidence.'] },
    'pennsylvania': { percent: 90, level: 'Advanced', tasks: ['Verify the final funding plan and any remaining gap after the RCTC delivery transition.', 'Track right-of-way, utility, environmental, bid, and construction-readiness milestones.', 'Add construction award, notice-to-proceed, change-order, and completion records when available.'] },
    'budget': { percent: 75, level: 'Developing', tasks: ['Add the adopted FY 2026–27 budget book, staff report, resolution, vote, and public summary.', 'Publish fund-level trends and comparisons between budgets, interim reports, and audited actuals.', 'Expand prior-year budgets, audits, amendments, debt results, and project-accounting reconciliations.'] },
    'police': { percent: 75, level: 'Developing', tasks: ['Reconcile Flock’s 30-day portal disclosure with Policy 465’s one-year server-retention language.', 'Add technology access audits, sharing records, usage statistics, complaints, and verified outcomes.', 'Complete staffing trends and police-station scope, funding, design, schedule, and construction records.'] },
    'downtown': { percent: 75, level: 'Developing', tasks: ['Reconcile GHD contract activity and payments before the terminated preliminary-design effort.', 'Reconcile CD03, R25-15, property, incentive, contract, expenditure, and remaining-balance records.', 'Track the short-term implementation goals directed in January 2026 and any later design, funding, mobility, or construction decisions.'] }
  };

  const filename = location.pathname.split('/').pop().replace(/\.html$/, '') || '';
  const page = document.body.dataset.page || '';
  const filenameKeys = { 'stewart-park': 'stewart-park', 'animal-control': 'animal-control', 'potrero-interchange': 'potrero', 'pennsylvania-grade-separation': 'pennsylvania', 'budget': 'budget', 'police': 'police', 'downtown-revitalization': 'downtown' };
  const key = filenameKeys[filename] || Object.keys(configs).find(name => page === name || page.startsWith(`${name}-`));
  const main = document.querySelector('main');
  if (!key || !main || document.querySelector('.center-completeness')) return;

  const config = configs[key];
  const tasks = config.tasks.map(task => `<li>${task}</li>`).join('');
  const section = document.createElement('section');
  section.className = 'center-completeness';
  section.setAttribute('aria-label', 'Intelligence Center completeness');
  section.innerHTML = `<div class="wrap"><details><summary><span><strong>Center completeness</strong><small>Published content and evidence coverage</small></span><span class="center-completeness-score"><strong>${config.percent}%</strong><small>${config.level}</small></span><span class="center-completeness-action">What remains <span aria-hidden="true">⌄</span></span></summary><div class="center-completeness-body"><div><strong>What this measures</strong><p>An editorial estimate of the center's published research, source coverage, historical context, and accountability reporting. It is not the City's project-completion percentage.</p></div><div><strong>Needed to complete this center</strong><ul>${tasks}</ul></div></div></details></div>`;

  const firstSection = main.querySelector(':scope > section');
  if (firstSection && (firstSection.classList.contains('budget-hero') || firstSection.classList.contains('project-section'))) firstSection.insertAdjacentElement('afterend', section);
  else main.insertAdjacentElement('afterbegin', section);
})();
