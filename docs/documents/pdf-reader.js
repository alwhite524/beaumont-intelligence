/* Shared, bounded-memory PDF reader for BI and MBF. */
(() => {
  let library;
  const sessions = new WeakMap();
  function clear(container) {
    const session = sessions.get(container);
    if (session) {
      session.closed = true;
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
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    status.textContent = 'Loading document…';
    controls.append(previous, next, original);
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
          canvas.style.cssText = `width:${width}px;max-width:100%;height:auto;display:block;margin:auto`;
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

