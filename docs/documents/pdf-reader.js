/* Shared PDF reader with continuous, bounded-memory page rendering. */
(() => {
  let library;
  const sessions = new WeakMap();
  const expandedViews = new WeakMap();
  function closeExpanded(container) {
    const state = expandedViews.get(container);
    if (!state) return;
    expandedViews.delete(container);
    document.body.classList.remove('pdf-reader-expanded');
    document.removeEventListener('fullscreenchange', state.onFullscreenChange);
    if (document.fullscreenElement === state.dialog) document.exitFullscreen().catch(() => {});
    state.marker.replaceWith(container);
    container.style.cssText = state.originalStyle;
    if (state.attachmentMarker) state.attachmentMarker.replaceWith(state.attachments);
    state.dialog.removeEventListener('close', state.onClose);
    if (state.dialog.open) state.dialog.close();
    state.dialog.remove();
    const controls = container.querySelector('.pdf-reader-controls');
    if (controls) {
      controls.querySelector('.pdf-reader-expand').hidden = false;
      controls.querySelector('.pdf-reader-collapse').hidden = true;
      controls.querySelector('.pdf-reader-expand').focus();
    }
  }
  function clear(container, preserveExpanded = false) {
    const session = sessions.get(container);
    if (session) {
      session.closed = true;
      session.observer?.disconnect();
      if (session.updateCounter) container.removeEventListener('scroll', session.updateCounter);
      session.task?.destroy().catch(() => {});
      sessions.delete(container);
    }
    if (!preserveExpanded) closeExpanded(container);
    container.replaceChildren();
    container.removeAttribute('aria-busy');
  }
  async function open(container, url, title, options = {}) {
    clear(container, true);
    expandedViews.get(container)?.dialog.setAttribute('aria-label', title + ' full screen viewer');
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
    const fullscreen = document.createElement('button');
    fullscreen.type = 'button';
    fullscreen.className = 'pdf-reader-expand';
    fullscreen.textContent = '⛶ Full screen';
    fullscreen.setAttribute('aria-label', 'Full screen');
    const original = document.createElement('a');
    original.href = options.startPage > 1 ? `${url}#page=${options.startPage}` : url;
    original.target = '_blank';
    original.rel = 'noopener';
    original.textContent = 'Open PDF in a new tab ↗';
    const collapse = document.createElement('button');
    collapse.type = 'button';
    collapse.className = 'pdf-reader-collapse';
    collapse.textContent = '↙ Collapse';
    collapse.setAttribute('aria-label', 'Collapse viewer');
    collapse.hidden = !expandedViews.has(container);
    fullscreen.hidden = expandedViews.has(container);
    controls.append(readerTitle, pageCounter, original, fullscreen, collapse);
    const status = document.createElement('p');
    status.className = 'pdf-reader-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Loading document…';
    const pages = document.createElement('div');
    pages.className = 'pdf-reader-pages';
    container.append(controls, status, pages);
    container.setAttribute('aria-busy', 'true');
    fullscreen.addEventListener('click', async () => {
      if (expandedViews.has(container)) return;
      const marker = document.createElement('span');
      container.before(marker);
      const dialog = document.createElement('dialog');
      dialog.className = 'pdf-reader-dialog';
      dialog.setAttribute('aria-label', title + ' full screen viewer');
      const attachments = container.parentElement?.querySelector('#viewer-attachments');
      const attachmentMarker = attachments ? document.createElement('span') : null;
      if (attachmentMarker) attachments.before(attachmentMarker);
      const state = { dialog, marker, originalStyle: container.style.cssText, attachments, attachmentMarker, native: false };
      state.onClose = () => closeExpanded(container);
      state.onFullscreenChange = () => {
        if (state.native && !document.fullscreenElement) closeExpanded(container);
      };
      expandedViews.set(container, state);
      container.style.cssText = 'flex:1 1 auto;width:100%;height:auto;min-height:0;max-height:none;max-width:none;border-radius:0;padding:0;box-sizing:border-box';
      document.body.append(dialog);
      dialog.append(container);
      if (attachments) dialog.append(attachments);
      dialog.addEventListener('close', state.onClose);
      dialog.showModal();
      document.body.classList.add('pdf-reader-expanded');
      fullscreen.hidden = true;
      collapse.hidden = false;
      collapse.focus();
      document.addEventListener('fullscreenchange', state.onFullscreenChange);
      if (document.fullscreenEnabled && dialog.requestFullscreen) {
        try {
          await dialog.requestFullscreen();
          if (expandedViews.get(container) === state) state.native = true;
        } catch { /* The viewport-filling modal still works. */ }
      }
    });
    collapse.addEventListener('click', () => closeExpanded(container));
    const fail = error => {
      if (session.closed) return;
      status.textContent = 'Inline viewing is unavailable. Use “Open PDF in a new tab” to read or save the document.';
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
      status.hidden = true;
      container.removeAttribute('aria-busy');
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
      let queue = Promise.resolve();
      const render = slot => {
        queue = queue.then(async () => {
          if (session.closed || !slot.isConnected || !slot.dataset.visible || slot.firstChild) return;
          const page = await pdf.getPage(Number(slot.dataset.page));
          if (session.closed || !slot.dataset.visible) { page.cleanup(); return; }
          const baseViewport = page.getViewport({ scale: 1 });
          const width = Math.max(1, Math.min(container.clientWidth - 24, 1200));
          const scale = Math.min(width / baseViewport.width * Math.min(window.devicePixelRatio || 1, 2), Math.sqrt(2000000 / (baseViewport.width * baseViewport.height)));
          const viewport = page.getViewport({ scale });
          const canvas = document.createElement('canvas');
          canvas.className = 'pdf-page-canvas';
          slot.dataset.rendering = 'true';
          canvas.width = Math.max(1, Math.floor(viewport.width));
          canvas.height = Math.max(1, Math.floor(viewport.height));
          canvas.setAttribute('role', 'img');
          canvas.setAttribute('aria-label', title + ', page ' + slot.dataset.page + ' of ' + pdf.numPages);
          slot.append(canvas);
          try {
            await page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport }).promise;
          } finally {
            delete slot.dataset.rendering;
            page.cleanup();
            if (session.closed || !slot.dataset.visible) { canvas.width = canvas.height = 0; canvas.remove(); }
          }
        }).catch(fail);
      };
      session.observer = new IntersectionObserver(entries => {
        for (const entry of entries) {
          const slot = entry.target;
          if (entry.isIntersecting) {
            slot.dataset.visible = 'true';
            render(slot);
          } else {
            delete slot.dataset.visible;
            const canvas = slot.querySelector('canvas');
            if (canvas && !slot.dataset.rendering) { canvas.width = canvas.height = 0; canvas.remove(); }
          }
        }
      }, { root: container, rootMargin: '600px 0px' });
      slots.forEach(slot => session.observer.observe(slot));
    } catch (error) { fail(error); }
  }
  window.BIPdfReader = { open, clear };
})();
