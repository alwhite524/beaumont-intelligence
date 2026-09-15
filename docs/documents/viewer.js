(() => {
  const params = new URLSearchParams(window.location.search);

  const title = document.querySelector("#document-title");
  const summary = document.querySelector("#document-summary");
  const meetingDate = document.querySelector("#meeting-date");
  const agendaItem = document.querySelector("#agenda-item");
  const category = document.querySelector("#category");
  const documentType = document.querySelector("#document-type");
  const attachments = document.querySelector("#attachments");
  const viewerBackLink = document.querySelector("#viewer-back-link");
  const briefingLink = document.querySelector("#briefing-link");
  const pdfPanel = document.querySelector(".inline-pdf-panel");
  const pdfViewer = document.querySelector("#pdf-viewer");
  const pdfClose = document.querySelector("#pdf-close");
  let lastOpenedDocumentId = null;
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
  const renderPdf = (url, documentTitle) => window.BIPdfReader.open(pdfViewer, url, documentTitle);

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

  const renderStandalone = (url) => {
    let filename = params.get("title") || "Official document";
    let sourceHost = "";
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
      sourceHost = parsedUrl.hostname;
      const pathName = decodeURIComponent(parsedUrl.pathname.split("/").pop() || "");
      if (!params.get("title") && pathName && !/filestream\.ashx$/i.test(pathName)) {
        filename = pathName.replace(/\.pdf$/i, "").replace(/[-_]+/g, " ");
      }
    } catch {
      renderDocument();
      return;
    }

    document.title = `${filename} | Beaumont Intelligence`;
    title.textContent = filename;
    summary.textContent = sourceHost === "documents.beaumontintelligence.com"
      ? "Archived official document hosted by Beaumont Intelligence."
      : "Official City document displayed through the Beaumont Intelligence viewer.";
    meetingDate.textContent = "See source record";
    agendaItem.textContent = "—";
    category.textContent = "Official record";
    documentType.textContent = "PDF";
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
    pdfPanel.hidden = false;
    pdfViewer.setAttribute("aria-label", `${filename} PDF`);
    renderPdf(url, filename);
  };

  attachments.addEventListener("click", (event) => {
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
  });

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
