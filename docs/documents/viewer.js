(() => {
  const params = new URLSearchParams(window.location.search);

  const title = document.querySelector("#document-title");
  const summary = document.querySelector("#document-summary");
  const meetingDate = document.querySelector("#meeting-date");
  const agendaItem = document.querySelector("#agenda-item");
  const category = document.querySelector("#category");
  const documentType = document.querySelector("#document-type");
  const attachments = document.querySelector("#attachments");
  const briefingLink = document.querySelector("#briefing-link");
  const pdfPanel = document.querySelector(".inline-pdf-panel");
  const pdfViewer = document.querySelector("#pdf-viewer");
  const pdfClose = document.querySelector("#pdf-close");
  let lastOpenedDocumentId = null;
  let pdfRenderToken = 0;
  let pdfJsPromise;

  const loadPdfJs = () => {
    if (!pdfJsPromise) {
      pdfJsPromise = import(
        "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.min.mjs"
      ).then((pdfjsLib) => {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.worker.min.mjs";
        return pdfjsLib;
      });
    }

    return pdfJsPromise;
  };

  const clearPdf = () => {
    pdfRenderToken += 1;
    pdfViewer.replaceChildren();
    pdfViewer.removeAttribute("aria-busy");
  };

  const renderPageImages = (pageImages, documentTitle) => {
    pdfRenderToken += 1;
    pdfViewer.replaceChildren();
    pdfViewer.removeAttribute("aria-busy");

    pageImages.forEach((src, index) => {
      const image = document.createElement("img");
      image.className = "pdf-page-image";
      image.src = src;
      image.alt = `${documentTitle}, page ${index + 1} of ${pageImages.length}`;
      image.loading = index === 0 ? "eager" : "lazy";
      image.decoding = "async";
      pdfViewer.appendChild(image);
    });
  };

  const renderPdf = async (url, documentTitle) => {
    const renderToken = ++pdfRenderToken;
    pdfViewer.setAttribute("aria-busy", "true");
    pdfViewer.innerHTML = '<p class="pdf-loading">Loading document…</p>';

    try {
      const pdfjsLib = await loadPdfJs();
      const pdf = await pdfjsLib.getDocument({ url }).promise;
      if (renderToken !== pdfRenderToken) return;

      pdfViewer.replaceChildren();

      for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
        if (renderToken !== pdfRenderToken) return;

        const page = await pdf.getPage(pageNumber);
        const baseViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.max(pdfViewer.clientWidth - 24, 280);
        const cssScale = availableWidth / baseViewport.width;
        const outputScale = Math.min(window.devicePixelRatio || 1, 2);
        const viewport = page.getViewport({ scale: cssScale * outputScale });
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d", { alpha: false });

        canvas.className = "pdf-page-canvas";
        canvas.width = Math.floor(viewport.width);
        canvas.height = Math.floor(viewport.height);
        canvas.style.width = `${Math.floor(viewport.width / outputScale)}px`;
        canvas.style.height = `${Math.floor(viewport.height / outputScale)}px`;
        canvas.setAttribute("aria-label", `${documentTitle}, page ${pageNumber} of ${pdf.numPages}`);
        pdfViewer.appendChild(canvas);

        await page.render({ canvasContext: context, viewport }).promise;
      }

      if (renderToken === pdfRenderToken) {
        pdfViewer.removeAttribute("aria-busy");
      }
    } catch (error) {
      if (renderToken !== pdfRenderToken) return;
      pdfViewer.removeAttribute("aria-busy");
      pdfViewer.innerHTML = '<p class="pdf-error">The document could not be displayed. Please close the viewer and try again.</p>';
      console.error("Unable to render PDF", error);
    }
  };

  const renderDocument = (documentId, updateHistory = false, openPdf = false) => {
    const record = documentLibrary.find(
      (item) => item.id === documentId
    );

    if (!record) {
      title.textContent = "Document not found";
      summary.textContent =
        "The requested document could not be found in the Official Source Library.";

      attachments.innerHTML =
        '<p><a href="index.html">Return to the Official Source Library →</a></p>';
      briefingLink.hidden = true;
      pdfPanel.hidden = true;
      clearPdf();

      return;
    }

    if (updateHistory) {
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.set("id", record.id);
      window.history.pushState({ documentId: record.id }, "", nextUrl);
    }

    document.title = `${record.title} | Beaumont Intelligence`;
    title.textContent = record.title;
    summary.textContent = record.summary;

    meetingDate.textContent = record.meetingLabel;
    agendaItem.textContent = record.agendaItem;
    category.textContent = record.category;
    documentType.textContent = record.documentType;

    briefingLink.hidden = false;
    briefingLink.href = record.briefing;
    if (openPdf) {
      lastOpenedDocumentId = record.id;
      pdfPanel.hidden = false;
      pdfViewer.setAttribute("aria-label", `${record.title} PDF`);
      if (record.pageImages) {
        renderPageImages(record.pageImages, record.title);
      } else {
        renderPdf(record.pdf, record.title);
      }
    } else {
      pdfPanel.hidden = true;
      clearPdf();
    }

    const documentCollection = documentLibrary.filter(
      (item) =>
        item.meetingLabel === record.meetingLabel &&
        item.agendaItem === record.agendaItem
    );

    attachments.innerHTML = documentCollection.length
      ? documentCollection
            .map(related => {

                const isCurrent = related.id === lastOpenedDocumentId;

                return `
                    <article class="card related-document-card"
                       data-document-card-id="${related.id}"
                       ${isCurrent ? 'aria-current="page"' : ""}>

                        <div class="meta">

                            ${related.documentType}

                        </div>

                        <h3>

                            ${related.title}

                        </h3>

                        <p>

                            ${related.summary}

                        </p>

                        <a class="text-link"
                           href="viewer.html?id=${encodeURIComponent(related.id)}"
                           data-document-id="${related.id}">View Document →</a>

                    </article>
                `;

            })

            .join("")
      : "<p>No documents available.</p>";
  };

  attachments.addEventListener("click", (event) => {
    const link = event.target.closest("[data-document-id]");
    if (!link) return;
    event.preventDefault();
    const documentId = link.dataset.documentId;
    const isCurrent = documentId === new URLSearchParams(window.location.search).get("id");
    renderDocument(documentId, !isCurrent, true);
    pdfPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  pdfClose.addEventListener("click", () => {
    pdfPanel.hidden = true;
    clearPdf();

    const lastOpenedCard = [...attachments.querySelectorAll("[data-document-id]")]
      .find((link) => link.dataset.documentId === lastOpenedDocumentId);

    if (lastOpenedCard) {
      lastOpenedCard.scrollIntoView({ behavior: "smooth", block: "center" });
      lastOpenedCard.focus({ preventScroll: true });
    }
  });

  window.addEventListener("popstate", () => {
    renderDocument(new URLSearchParams(window.location.search).get("id"));
  });

  renderDocument(params.get("id"));
})();
