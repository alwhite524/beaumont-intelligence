document.addEventListener('DOMContentLoaded', () => {
  const sourceKey = Object.keys(window).find(key => /^BI_.+_SOURCES$/.test(key));
  const documents = sourceKey ? window[sourceKey] : [];
  const dialog = document.querySelector('#viewer-dialog');
  const frame = document.querySelector('#viewer-frame');
  const viewerTitle = document.querySelector('#viewer-title');
  if (!documents.length || !dialog || !frame) return;

  const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);

  document.querySelectorAll('.outcome').forEach(card => {
    const item = card.querySelector('.meta')?.textContent.split('·')[0].trim();
    const itemDocuments = documents.filter(document => document.item === item);
    if (!itemDocuments.length) return;
    const section = document.createElement('details');
    section.className = 'outcome-documents';
    section.innerHTML = `<summary>Official documents · ${itemDocuments.length}</summary><div>${itemDocuments.map(document => `<button type="button" data-record-url="${escapeHtml(document.archiveUrl)}" data-record-title="${escapeHtml(document.title)}">${escapeHtml(document.title)}</button>`).join('')}</div>`;
    card.append(section);
  });

  document.querySelectorAll('#calendar-results > .calendar').forEach(calendar => {
    if (!calendar.querySelector('summary')?.textContent.startsWith('Consent')) calendar.remove();
  });
  const calendarSection = document.querySelector('#calendar-results')?.closest('section');
  if (calendarSection) {
    const heading = calendarSection.querySelector('h2');
    const description = calendarSection.querySelector('h2 + p');
    if (heading) heading.textContent = 'Consent calendar documents';
    if (description) description.textContent = 'Expand the consent calendar and an item to open every archived staff report and attachment.';
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-record-url]');
    if (!button) return;
    viewerTitle.textContent = button.dataset.recordTitle;
    const returnUrl = location.href;
    frame.src = `../documents/viewer.html?url=${encodeURIComponent(button.dataset.recordUrl)}&title=${encodeURIComponent(button.dataset.recordTitle)}&returnUrl=${encodeURIComponent(returnUrl)}&returnLabel=${encodeURIComponent('Back to meeting record')}`;
    dialog.showModal();
  });
});
