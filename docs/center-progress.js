(() => {
  const configs = {
    'stewart-park': { percent: 97, level: 'Advanced', tasks: ['Add Phase I and Phase II substantial-completion, punch-list, closeout, and Council acceptance records as construction finishes.', 'Reconcile actual project expenditures, change orders, ORLP reimbursements, retained balances, and final funding by phase.', 'Publish completed-feature verification, opening dates, and post-construction use and maintenance outcomes.'] },
    'animal-control': { percent: 80, level: 'Strong', tasks: ['Add current service-volume, response-time, sheltering, and outcome trends.', 'Track municipal-shelter design, construction cost, operating plan, and transition milestones.', 'Complete multi-year staffing, contract-performance, complaint, and enforcement records.'] },
    'potrero': { percent: 85, level: 'Strong', tasks: ['Verify the current delivery and construction schedule through primary records.', 'Reconcile grants, local contributions, contracts, amendments, expenditures, and remaining need.', 'Add construction milestones, traffic impacts, change orders, and completion evidence.'] },
    'pennsylvania': { percent: 90, level: 'Advanced', tasks: ['Verify the final funding plan and any remaining gap after the RCTC delivery transition.', 'Track right-of-way, utility, environmental, bid, and construction-readiness milestones.', 'Add construction award, notice-to-proceed, change-order, and completion records when available.'] },
    'budget': { percent: 75, level: 'Developing', tasks: ['Add the adopted FY 2026–27 budget book, staff report, resolution, vote, and public summary.', 'Publish fund-level trends and comparisons between budgets, interim reports, and audited actuals.', 'Expand prior-year budgets, audits, amendments, debt results, and project-accounting reconciliations.'] },
    'police': { percent: 90, level: 'Advanced', tasks: ['Complete current sworn authorized-versus-filled staffing, vacancies, shift deployment, multi-year workload, response-time, clearance, use-of-force, and complaint trends.', 'Obtain the new station’s current parcel record, space program, LPA scope and deliverables, estimate basis, financing strategy, environmental path, delivery method, and schedule.', 'Complete technology implementation, audit, complaint, retention, data-sharing, invoice, and measured-outcome records.'] },
    'downtown': { percent: 85, level: 'Strong', tasks: ['Reconcile GHD contract activity and payments before the terminated preliminary-design effort.', 'Complete the project-level reconciliation behind the January 2026 spending summary, including CD03 and related property accounts.', 'Track the measured implementation program directed in January 2026 and any later design, funding, mobility, or construction decisions.'] }
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
