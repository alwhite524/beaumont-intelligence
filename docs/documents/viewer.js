(() => {
  const params = new URLSearchParams(window.location.search);

  const title = document.querySelector("#document-title");
  const summary = document.querySelector("#document-summary");
  const attachments = document.querySelector("#attachments");
  const viewerAttachments = document.querySelector("#viewer-attachments");
  const viewerBackLink = document.querySelector("#viewer-back-link");
  const briefingLink = document.querySelector("#briefing-link");
  const pdfPanel = document.querySelector(".inline-pdf-panel");
  const pdfHeading = document.querySelector("#pdf-heading");
  const pdfViewer = document.querySelector("#pdf-viewer");
  const pdfClose = document.querySelector("#pdf-close");
  let lastOpenedDocumentId = null;
  let activeStandaloneUrl = null;
  const sourceLists = new Map();
  const returnUrl = params.get("returnUrl");
  const returnLabel = params.get("returnLabel");

  if (returnUrl) {
    viewerBackLink.href = returnUrl;
    viewerBackLink.textContent = `← ${returnLabel || "Back to previous page"}`;
  } else try {
    const previousUrl = new URL(document.referrer);
    if (previousUrl.origin === window.location.origin) {
      viewerBackLink.href = previousUrl.href;
    }
  } catch {
    viewerBackLink.href = "index.html";
  }

  viewerBackLink.addEventListener("click", (event) => {
    if (!returnUrl && document.referrer && window.history.length > 1) {
      event.preventDefault();
      window.history.back();
    }
  });

  const clearPdf = () => window.BIPdfReader.clear(pdfViewer);
  const renderPageImages = (images, documentTitle) => {
    clearPdf();
    images.forEach((src, index) => {
      const image = document.createElement('img');
      image.className = 'pdf-page-image'; image.src = src;
      image.alt = `${documentTitle}, page ${index + 1} of ${images.length}`;
      image.loading = index ? 'lazy' : 'eager'; pdfViewer.appendChild(image);
    });
  };
  const requestedPage = Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1);
  const renderPdf = (url, documentTitle) => window.BIPdfReader.open(
    pdfViewer, url, documentTitle, { startPage: requestedPage }
  );

  const renderDocument = (documentId, updateHistory = false, openPdf = false) => {
    activeStandaloneUrl = null;
    const record = documentLibrary.find(
      (item) => item.id === documentId
    );

    if (!record) {
      title.textContent = "Document not found";
      summary.textContent =
        "The requested document could not be found in the Official Source Library.";
      summary.hidden = false;

      attachments.innerHTML =
        '<p><a href="index.html">Return to the Official Source Library →</a></p>';
      briefingLink.hidden = true;
      pdfPanel.hidden = true;
      viewerAttachments.hidden = true;
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
    summary.hidden = !record.summary;

    briefingLink.hidden = false;
    briefingLink.href = record.briefing;
    if (openPdf) {
      lastOpenedDocumentId = record.id;
      pdfPanel.hidden = false;
      pdfHeading.textContent = record.title;
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
    const otherDocuments = documentCollection.filter(item => item.id !== record.id);
    viewerAttachments.replaceChildren();
    viewerAttachments.hidden = !openPdf || !otherDocuments.length;
    if (openPdf && otherDocuments.length) {
      const label = document.createElement("strong");
      label.textContent = "Other attachments";
      viewerAttachments.append(label);
      otherDocuments.forEach(item => {
        const link = document.createElement("a");
        link.href = `viewer.html?id=${encodeURIComponent(item.id)}`;
        link.dataset.documentId = item.id;
        link.textContent = item.title;
        viewerAttachments.append(link);
      });
    }

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

  const relatedSources = (url) => {
    let parsed;
    try { parsed = new URL(url); } catch { return Promise.resolve([]); }
    const match = parsed.hostname === "documents.beaumontintelligence.com"
      ? parsed.pathname.match(/^\/official-documents\/(\d{4}-\d{2}-\d{2})\//)
      : null;
    if (!match) return Promise.resolve([]);
    const date = match[1];
    if (!sourceLists.has(date)) {
      sourceLists.set(date, new Promise(resolve => {
        const script = document.createElement("script");
        script.src = `../briefings/${date}-sources.js`;
        script.onload = () => {
          const list = Object.keys(window)
            .filter(key => /^BI_.*_SOURCES$/.test(key) && Array.isArray(window[key]))
            .map(key => window[key])
            .find(items => items.some(item => item.archiveUrl === url));
          resolve(list || []);
        };
        script.onerror = () => resolve([]);
        document.head.append(script);
      }));
    }
    return sourceLists.get(date).then(items => {
      const current = items.find(item => item.archiveUrl === url);
      return current ? items.filter(item => item.item === current.item && item.archiveUrl !== url) : [];
    });
  };

  const renderStandalone = (url, suppliedTitle = null, updateHistory = false) => {
    let filename = suppliedTitle || params.get("title") || "Official document";
    try {
      const parsedUrl = new URL(url);
      const trustedHosts = new Set([
        "documents.beaumontintelligence.com",
        "pub-beaumont.escribemeetings.com",
        "beaumontca.gov",
        "www.beaumontca.gov",
      ]);
      if (parsedUrl.protocol !== "https:" || !trustedHosts.has(parsedUrl.hostname)) {
        throw new Error("Unsupported document host");
      }
      const pathName = decodeURIComponent(parsedUrl.pathname.split("/").pop() || "");
      if (!params.get("title") && pathName && !/filestream\.ashx$/i.test(pathName)) {
        filename = pathName.replace(/\.pdf$/i, "").replace(/[-_]+/g, " ");
      }
    } catch {
      renderDocument();
      return;
    }

    document.title = `${filename} | Beaumont Intelligence`;
    activeStandaloneUrl = url;
    if (updateHistory) {
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.set("url", url);
      nextUrl.searchParams.set("title", filename);
      window.history.pushState({ standaloneUrl: url }, "", nextUrl);
    }
    title.textContent = filename;
    summary.textContent = "";
    summary.hidden = true;
    briefingLink.hidden = true;
    attachments.replaceChildren();
    const actionsParagraph = document.createElement("p");
    const viewLink = document.createElement("a");
    viewLink.href = "#pdf-heading";
    viewLink.className = "text-link";
    viewLink.dataset.standaloneUrl = url;
    viewLink.dataset.documentTitle = filename;
    viewLink.textContent = "Reopen in viewer →";
    actionsParagraph.appendChild(viewLink);
    actionsParagraph.append(" · ");
    const downloadLink = document.createElement("a");
    downloadLink.href = url;
    downloadLink.download = "";
    downloadLink.textContent = "Download PDF →";
    actionsParagraph.appendChild(downloadLink);
    attachments.appendChild(actionsParagraph);
    viewerAttachments.replaceChildren();
    viewerAttachments.hidden = true;
    pdfPanel.hidden = false;
    pdfHeading.textContent = filename;
    pdfViewer.setAttribute("aria-label", `${filename} PDF`);
    renderPdf(url, filename);
    relatedSources(url).then(otherDocuments => {
      if (activeStandaloneUrl !== url) return;
      viewerAttachments.replaceChildren();
      viewerAttachments.hidden = !otherDocuments.length;
      if (!otherDocuments.length) return;
      const label = document.createElement("strong");
      label.textContent = "Other attachments";
      viewerAttachments.append(label);
      otherDocuments.forEach(item => {
        const link = document.createElement("a");
        link.href = `viewer.html?url=${encodeURIComponent(item.archiveUrl)}&title=${encodeURIComponent(item.title)}`;
        link.dataset.switchUrl = item.archiveUrl;
        link.dataset.documentTitle = item.title;
        link.textContent = item.title;
        viewerAttachments.append(link);
      });
    });
  };

  const handleAttachmentClick = (event) => {
    const switchLink = event.target.closest("[data-switch-url]");
    if (switchLink) {
      event.preventDefault();
      renderStandalone(switchLink.dataset.switchUrl, switchLink.dataset.documentTitle, true);
      pdfPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const standaloneLink = event.target.closest("[data-standalone-url]");
    if (standaloneLink) {
      event.preventDefault();
      pdfPanel.hidden = false;
      renderPdf(
        standaloneLink.dataset.standaloneUrl,
        standaloneLink.dataset.documentTitle || "Official document"
      );
      pdfPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    const link = event.target.closest("[data-document-id]");
    if (!link) return;
    event.preventDefault();
    const documentId = link.dataset.documentId;
    const isCurrent = documentId === new URLSearchParams(window.location.search).get("id");
    renderDocument(documentId, !isCurrent, true);
    pdfPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  attachments.addEventListener("click", handleAttachmentClick);
  viewerAttachments.addEventListener("click", handleAttachmentClick);

  pdfClose.addEventListener("click", () => {
    pdfPanel.hidden = true;
    clearPdf();

    const lastOpenedCard = [...attachments.querySelectorAll("[data-document-id]")]
      .find((link) => link.dataset.documentId === lastOpenedDocumentId);

    const standaloneLink = attachments.querySelector("[data-standalone-url]");

    if (lastOpenedCard) {
      lastOpenedCard.scrollIntoView({ behavior: "smooth", block: "center" });
      lastOpenedCard.focus({ preventScroll: true });
    } else if (standaloneLink) {
      standaloneLink.scrollIntoView({ behavior: "smooth", block: "center" });
      standaloneLink.focus({ preventScroll: true });
    }
  });

  window.addEventListener("popstate", () => {
    const historyParams = new URLSearchParams(window.location.search);
    if (historyParams.get("url")) {
      renderStandalone(historyParams.get("url"), historyParams.get("title"));
      return;
    }
    const historyPdf = historyParams.get("pdf");
    const historyRecord = historyPdf
      ? documentLibrary.find((item) => item.pdf.endsWith(`/official-documents/${historyPdf}`))
      : null;
    renderDocument(historyParams.get("id") || historyRecord?.id);
  });

  const requestedPdf = params.get("pdf");
  const requestedUrl = params.get("url");
  const requestedRecord = requestedPdf
    ? documentLibrary.find((item) => item.pdf.endsWith(`/official-documents/${requestedPdf}`))
    : null;

  if (requestedUrl) renderStandalone(requestedUrl);
  else renderDocument(
    params.get("id") || requestedRecord?.id,
    false,
    Boolean(requestedPdf && requestedRecord)
  );
})();
