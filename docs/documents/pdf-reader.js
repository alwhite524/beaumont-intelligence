/* Shared PDF reader with continuous, bounded-memory page rendering. */
(() => {
  let library;
  const sessions = new WeakMap();
  function clear(container) {
    const session = sessions.get(container);
    if (session) {
      session.closed = true;
      session.observer?.disconnect();
      if (session.updateCounter) container.removeEventListener('scroll', session.updateCounter);
      session.task?.destroy().catch(() => {});
      sessions.delete(container);
    }
    container.replaceChildren();
    container.removeAttribute('aria-busy');
  }
  async function open(container, url, title, options = {}) {
    clear(container);
    const session = { closed: false };
    sessions.set(container, session);
    const controls = document.createElement('div');
    controls.className = 'pdf-reader-controls';
    const readerTitle = document.createElement('span');
    readerTitle.className = 'pdf-reader-title';
    readerTitle.textContent = title;
    const pageCounter = document.createElement('span');
    pageCounter.className = 'pdf-reader-counter';
    pageCounter.setAttribute('aria-live', 'polite');
    pageCounter.textContent = 'Loading…';
    const original = document.createElement('a');
    original.href = options.startPage > 1 ? `${url}#page=${options.startPage}` : url;
    original.target = '_blank';
    original.rel = 'noopener';
    original.textContent = 'Open PDF in a new tab ↗';
    original.hidden = true;
    const archived = !/^[a-z][a-z\d+.-]*:/i.test(url) ||
      /^https:\/\/documents\.beaumontintelligence\.com\//i.test(url) ||
      url.startsWith(`${window.location?.origin}/`);
    controls.append(readerTitle, pageCounter);
    if (!archived) controls.append(original);
    const status = document.createElement('p');
    status.className = 'pdf-reader-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Loading document…';
    const pages = document.createElement('div');
    pages.className = 'pdf-reader-pages';
    container.append(controls, status, pages);
    container.setAttribute('aria-busy', 'true');
    const fail = error => {
      if (session.closed) return;
      status.textContent = archived
        ? 'The archived PDF could not be displayed. Reload this page to try again.'
        : 'Inline viewing is unavailable. Use “Open PDF in a new tab” to open the source.';
      if (!archived) original.hidden = false;
      status.hidden = false;
      pageCounter.textContent = 'Unavailable';
      container.removeAttribute('aria-busy');
      console.error('Unable to display PDF', error?.name, error?.message, error?.details);
    };
    try {
      if (!library) library = import('https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/legacy/build/pdf.min.mjs')
        .then(lib => { lib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/legacy/build/pdf.worker.min.mjs'; return lib; })
        .catch(error => { library = null; throw error; });
      const lib = await library;
      if (session.closed) return;
      session.task = lib.getDocument({ url });
      const pdf = await session.task.promise;
      if (session.closed) return;
      const first = Math.max(1, Math.min(options.startPage || 1, pdf.numPages));
      const last = Math.max(first, Math.min(options.endPage || pdf.numPages, pdf.numPages));
      const firstPage = await pdf.getPage(first);
      const base = firstPage.getViewport({ scale: 1 });
      firstPage.cleanup();
      const slots = [];
      for (let number = first; number <= last; number++) {
        const slot = document.createElement('div');
        slot.className = 'pdf-reader-page';
        slot.style.aspectRatio = base.width + ' / ' + base.height;
        slot.dataset.page = number;
        slot.setAttribute('aria-label', title + ', page ' + number + ' of ' + pdf.numPages);
        pages.append(slot);
        slots.push(slot);
      }
      pageCounter.textContent = 'Page ' + first + ' of ' + pdf.numPages;
      const updateCounter = () => {
        if (session.closed) return;
        const visibleTop = container.getBoundingClientRect().top + controls.offsetHeight;
        let current = slots[0];
        for (const slot of slots) {
          if (slot.getBoundingClientRect().top <= visibleTop + 32) current = slot;
          else break;
        }
        pageCounter.textContent = 'Page ' + current.dataset.page + ' of ' + pdf.numPages;
      };
      container.addEventListener('scroll', updateCounter, { passive: true });
      session.updateCounter = updateCounter;
      const shouldRender = slot => !session.closed && slot.isConnected &&
        (slot === slots[0] || Boolean(slot.dataset.visible));
      const render = async slot => {
        if (!shouldRender(slot) || slot.firstChild) return;
        const page = await pdf.getPage(Number(slot.dataset.page));
        if (!shouldRender(slot)) { page.cleanup(); return; }
        const baseViewport = page.getViewport({ scale: 1 });
        const width = Math.max(1, Math.min(container.clientWidth - 24, 1200));
        const scale = Math.min(width / baseViewport.width * Math.min(window.devicePixelRatio || 1, 2), Math.sqrt(2000000 / (baseViewport.width * baseViewport.height)));
        const viewport = page.getViewport({ scale });
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page-canvas';
        canvas.width = Math.max(1, Math.floor(viewport.width));
        canvas.height = Math.max(1, Math.floor(viewport.height));
        canvas.setAttribute('role', 'img');
        canvas.setAttribute('aria-label', title + ', page ' + slot.dataset.page + ' of ' + pdf.numPages);
        try {
          await page.render({ canvas, viewport }).promise;
          if (shouldRender(slot)) slot.append(canvas);
        } finally {
          page.cleanup();
          if (!canvas.isConnected) canvas.width = canvas.height = 0;
        }
      };
      // Paint the requested page even if visibility callbacks are delayed in an iframe.
      await render(slots[0]);
      if (session.closed) return;
      status.hidden = true;
      container.removeAttribute('aria-busy');

      let queue = Promise.resolve();
      session.observer = new IntersectionObserver(entries => {
        for (const entry of entries) {
          const slot = entry.target;
          if (entry.isIntersecting) {
            slot.dataset.visible = 'true';
            queue = queue.then(() => render(slot)).catch(fail);
          } else {
            delete slot.dataset.visible;
            const canvas = slot.querySelector('canvas');
            if (canvas) { canvas.width = canvas.height = 0; canvas.remove(); }
          }
        }
      }, { root: container, rootMargin: '600px 0px' });
      slots.slice(1).forEach(slot => session.observer.observe(slot));
    } catch (error) { fail(error); }
  }
  window.BIPdfReader = { open, clear };
})();
