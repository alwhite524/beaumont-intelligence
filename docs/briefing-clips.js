(() => {
  const toSeconds = value => {
    const parts = value.split(':').map(Number);
    if (parts.some(Number.isNaN) || parts.length < 2 || parts.length > 3) return null;
    return parts.reduce((total, part) => total * 60 + part, 0);
  };
  const fromSeconds = value => {
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = value % 60;
    return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}` : `${minutes}:${String(seconds).padStart(2, '0')}`;
  };
  const meetingVideo = [...document.querySelectorAll('a[href*="youtube.com/watch"]')].map(link => {
    try { return new URL(link.href).searchParams.get('v'); } catch { return null; }
  }).find(Boolean);
  if (!meetingVideo) return;

  document.querySelectorAll('.agenda-item .after-grid').forEach(summary => {
    const videoValue = [...summary.querySelectorAll('div')].find(item => item.querySelector('strong')?.textContent.trim() === 'Video')?.querySelector('span');
    if (!videoValue || videoValue.querySelector('a')) return;
    const match = videoValue.textContent.match(/(\d{1,2}:\d{2}(?::\d{2})?)\s*[·–-]\s*Vote\s+(\d{1,2}:\d{2}(?::\d{2})?)/i);
    if (!match) return;
    const start = toSeconds(match[1]);
    const vote = toSeconds(match[2]);
    if (start === null || vote === null || vote < start) return;

    const end = vote + 30;
    const item = summary.closest('.agenda-item');
    const title = item?.querySelector('h3')?.textContent.trim() || 'Council discussion';
    const params = new URLSearchParams({
      video: meetingVideo,
      start: String(start),
      end: String(end),
      title,
      range: `${match[1]}–${fromSeconds(end)}`,
      return: `${location.pathname.split('/').pop()}#${item?.id || ''}`
    });
    videoValue.innerHTML = `<a href="video-viewer.html?${params}">${match[1]}–${fromSeconds(end)} →</a>`;
  });

  const wrapAccordion = (node, title, additionalNode = null) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'accordion';
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    const content = document.createElement('div');
    summary.textContent = title;
    while (node.firstChild) content.appendChild(node.firstChild);
    if (additionalNode) content.appendChild(additionalNode);
    details.append(summary, content);
    wrapper.appendChild(details);
    node.replaceWith(wrapper);
  };

  document.querySelectorAll('article.agenda-item').forEach((article, index) => {
    const body = article.querySelector(':scope > .agenda-item-body');
    const rank = article.querySelector(':scope > .agenda-rank');
    const heading = body?.querySelector(':scope > h3');
    if (!body || !rank || !heading) return;

    body.querySelectorAll(':scope > .bi-insight').forEach(panel => {
      const label = panel.querySelector(':scope > strong');
      const title = label?.textContent.trim() || 'Key points';
      label?.remove();
      wrapAccordion(panel, title);
    });

    body.querySelectorAll(':scope > p').forEach(paragraph => {
      const label = paragraph.querySelector(':scope > strong:first-child');
      const title = label?.textContent.replace(/:$/, '').trim();
      if (!['What to watch', 'Fiscal impact', 'Why it matters', 'Plain English'].includes(title)) return;
      label.remove();
      wrapAccordion(paragraph, title);
    });

    body.querySelectorAll(':scope > .official-documents-heading').forEach(docHeading => {
      const actions = docHeading.nextElementSibling?.classList.contains('doc-actions') ? docHeading.nextElementSibling : null;
      const holder = document.createElement('div');
      if (actions) holder.appendChild(actions);
      docHeading.textContent = '';
      wrapAccordion(docHeading, 'Official documents', holder);
    });

    body.querySelectorAll(':scope > .official-documents').forEach(documents => {
      documents.querySelector(':scope > .official-documents-title')?.remove();
      wrapAccordion(documents, 'Official documents');
    });

    body.querySelectorAll(':scope > .questions-list').forEach(questions => {
      wrapAccordion(questions, 'Questions to track');
    });

    const details = document.createElement('details');
    details.className = `${article.className} dossier-technology-card`;
    details.id = article.id;
    details.setAttribute('name', 'briefing-card');
    if (index === 0) details.open = true;

    const summary = document.createElement('summary');
    const summaryHeading = document.createElement('span');
    const strong = document.createElement('strong');
    summaryHeading.className = 'dossier-card-heading';
    strong.textContent = heading.textContent.trim();
    summaryHeading.append(strong, document.createElement('i'));
    heading.remove();
    summary.append(rank, summaryHeading);
    details.append(summary, body);
    article.replaceWith(details);
  });
})();
