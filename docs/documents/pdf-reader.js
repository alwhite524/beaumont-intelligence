/* Shared PDF reader with continuous, bounded-memory page rendering. */
(() => {
  let library;
  const sessions = new WeakMap();
  function clear(container) {
    const session = sessions.get(container);
    if (session) {
      session.closed = true;
      session.observer?.disconnect();
      session.closeExpanded?.();
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
    const fullscreen = document.createElement('button');
    fullscreen.type = 'button';
    fullscreen.textContent = '⛶ Full screen';
    fullscreen.setAttribute('aria-label', 'Full screen');
    const original = document.createElement('a');
    original.href = url;
    original.target = '_blank';
    original.rel = 'noopener';
    original.textContent = 'Open PDF in a new tab ↗';
    const collapse = document.createElement('button');
    collapse.type = 'button';
    collapse.textContent = '↙ Collapse';
    collapse.setAttribute('aria-label', 'Collapse viewer');
    collapse.hidden = true;
    controls.append(fullscreen, original, collapse);
    const status = document.createElement('p');
    status.className = 'pdf-reader-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Loading document…';
    const pages = document.createElement('div');
    pages.className = 'pdf-reader-pages';
    container.append(controls, status, pages);
    container.setAttribute('aria-busy', 'true');
    let expanded = null;
    const closeExpanded = () => {
      if (!expanded) return;
      const { dialog, marker, originalStyle } = expanded;
      expanded = null;
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      if (document.fullscreenElement === dialog) document.exitFullscreen().catch(() => {});
      marker.replaceWith(container);
      container.style.cssText = originalStyle;
      dialog.removeEventListener('close', closeExpanded);
      dialog.close();
      dialog.remove();
      fullscreen.hidden = false;
      collapse.hidden = true;
      if (!session.closed) fullscreen.focus();
    };
    const onFullscreenChange = () => {
      if (expanded?.native && !document.fullscreenElement) closeExpanded();
    };
    session.closeExpanded = closeExpanded;
    fullscreen.addEventListener('click', async () => {
      const marker = document.createElement('span');
      container.before(marker);
      const dialog = document.createElement('dialog');
      dialog.className = 'pdf-reader-dialog';
      dialog.setAttribute('aria-label', title + ' full screen viewer');
      expanded = { dialog, marker, originalStyle: container.style.cssText, native: false };
      container.style.cssText = 'width:100%;height:100%;min-height:0;max-height:none;max-width:none;border-radius:0;padding:0;box-sizing:border-box';
      document.body.append(dialog);
      dialog.append(container);
      dialog.addEventListener('close', closeExpanded);
      dialog.showModal();
      fullscreen.hidden = true;
      collapse.hidden = false;
      collapse.focus();
      document.addEventListener('fullscreenchange', onFullscreenChange);
      if (document.fullscreenEnabled && dialog.requestFullscreen) {
        try {
          const state = expanded;
          await dialog.requestFullscreen();
          if (expanded === state) state.native = true;
        } catch { /* The viewport-filling modal still works. */ }
      }
    });
    collapse.addEventListener('click', closeExpanded);
    const fail = error => {
      if (session.closed) return;
      status.textContent = 'Inline viewing is unavailable. Use “Open PDF in a new tab” to read or save the document.';
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
      status.textContent = (last - first + 1) + ' page' + (last === first ? '' : 's') + ' · Scroll to read';
      container.removeAttribute('aria-busy');
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
