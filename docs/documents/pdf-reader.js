/* Shared, bounded-memory PDF reader for BI and MBF. */
(() => {
  let library;
  const sessions = new WeakMap();
  function clear(container) {
    const session = sessions.get(container);
    if (session) {
      session.closed = true;
      session.closeExpanded?.();
      session.render?.cancel();
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
    controls.style.cssText = 'display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:12px 0';
    const original = document.createElement('a');
    original.href = url;
    original.target = '_blank';
    original.rel = 'noopener';
    original.textContent = 'Open PDF in a new tab';
    const previous = document.createElement('button');
    previous.type = 'button'; previous.textContent = 'Previous page';
    const next = document.createElement('button');
    next.type = 'button'; next.textContent = 'Next page';
    previous.disabled = next.disabled = true;
    const fullscreen = document.createElement('button');
    fullscreen.type = 'button';
    fullscreen.textContent = 'Full screen';
    fullscreen.setAttribute('aria-pressed', 'false');
    let expanded = null;
    const closeExpanded = () => {
      if (!expanded) return;
      const { dialog, marker, originalStyle } = expanded;
      expanded = null;
      document.removeEventListener('fullscreenchange', onFullscreenChange);
      if (document.fullscreenElement === dialog) document.exitFullscreen().catch(() => {});
      marker.replaceWith(container);
      container.style.cssText = originalStyle;
      dialog.close();
      dialog.remove();
      fullscreen.textContent = 'Full screen';
      fullscreen.setAttribute('aria-pressed', 'false');
      if (!session.closed) fullscreen.focus();
    };
    const onFullscreenChange = () => {
      if (expanded?.native && !document.fullscreenElement) closeExpanded();
    };
    session.closeExpanded = closeExpanded;
    fullscreen.addEventListener('click', async () => {
      if (expanded) { closeExpanded(); return; }
      const marker = document.createElement('span');
      container.before(marker);
      const dialog = document.createElement('dialog');
      dialog.setAttribute('aria-label', `${title} full screen viewer`);
      dialog.style.cssText = 'position:fixed;inset:0;margin:0;width:100vw;height:100dvh;max-width:none;max-height:none;box-sizing:border-box;border:0;padding:16px;background:white;color:#172b45;overflow:auto';
      expanded = { dialog, marker, originalStyle: container.style.cssText, native: false };
      container.style.cssText = 'width:100%;max-width:1200px;margin:auto';
      document.body.append(dialog);
      dialog.append(container);
      dialog.addEventListener('close', closeExpanded);
      dialog.showModal();
      fullscreen.textContent = 'Exit full screen';
      fullscreen.setAttribute('aria-pressed', 'true');
      fullscreen.focus();
      document.addEventListener('fullscreenchange', onFullscreenChange);
      // A modal filling the viewport remains usable on iPhones and inside
      // agenda iframes where the Fullscreen API is unavailable or denied.
      if (document.fullscreenEnabled && dialog.requestFullscreen) {
        try {
          const state = expanded;
          await dialog.requestFullscreen();
          if (expanded === state) state.native = true;
        } catch { /* Keep the expanded modal. */ }
      }
    });
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    status.textContent = 'Loading document…';
    controls.append(previous, next, fullscreen, original);
    const pages = document.createElement('div');
    container.append(controls, status, pages);
    container.setAttribute('aria-busy', 'true');
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
      let current = first;
      async function show(number) {
        previous.disabled = next.disabled = true;
        container.setAttribute('aria-busy', 'true');
        try {
          const page = await pdf.getPage(number);
          if (session.closed) return;
          pages.querySelectorAll('canvas').forEach(canvas => { canvas.width = canvas.height = 0; });
          pages.replaceChildren();
          const base = page.getViewport({ scale: 1 });
          const width = Math.max(1, Math.min(container.clientWidth || 320, 1200) - 24);
          const cssScale = width / base.width;
          // Cap individual canvas area as well as retaining only one page.
          const scale = Math.min(cssScale * Math.min(window.devicePixelRatio || 1, 2), Math.sqrt(2000000 / (base.width * base.height)));
          const viewport = page.getViewport({ scale });
          const canvas = document.createElement('canvas');
          canvas.className = 'pdf-page-canvas';
          canvas.width = Math.max(1, Math.floor(viewport.width));
          canvas.height = Math.max(1, Math.floor(viewport.height));
          canvas.style.cssText = 'width:100%;max-width:1200px;height:auto;display:block;margin:auto';
          canvas.setAttribute('role', 'img');
          canvas.setAttribute('aria-label', `${title}, page ${number} of ${pdf.numPages}`);
          pages.append(canvas);
          session.render = page.render({ canvasContext: canvas.getContext('2d', { alpha: false }), viewport });
          await session.render.promise;
          if (session.closed) return;
          page.cleanup();
          current = number;
          status.textContent = `Page ${number} of ${pdf.numPages}` + (first !== 1 || last !== pdf.numPages ? ` · selected pages ${first}–${last}` : '');
        } catch (error) { fail(error); }
        finally {
          if (!session.closed) {
            previous.disabled = current <= first;
            next.disabled = current >= last;
            container.removeAttribute('aria-busy');
          }
        }
      }
      previous.addEventListener('click', () => show(current - 1));
      next.addEventListener('click', () => show(current + 1));
      await show(current);
    } catch (error) { fail(error); }
  }
  window.BIPdfReader = { open, clear };
})();

