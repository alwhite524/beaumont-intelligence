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
  const pdfLink = document.querySelector("#pdf-link");
  const pdfViewer = document.querySelector("#pdf-viewer");

  const renderDocument = (documentId, updateHistory = false) => {
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
      pdfLink.hidden = true;
      pdfViewer.hidden = true;

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
    pdfLink.hidden = false;
    pdfLink.href = record.pdf;
    pdfLink.target = "_blank";
    pdfLink.rel = "noopener";
    pdfViewer.hidden = false;
    pdfViewer.src = record.pdf;
    pdfViewer.title = `${record.title} PDF`;

    const documentCollection = documentLibrary.filter(
      (item) =>
        item.meetingLabel === record.meetingLabel &&
        item.agendaItem === record.agendaItem
    );

    if (documentCollection.length > 1) {

      attachments.innerHTML =
        documentCollection
            .map(related => {

                const isCurrent = related.id === record.id;

                return `
                    <a class="card related-document-card"
                       href="viewer.html?id=${encodeURIComponent(related.id)}"
                       data-document-id="${related.id}"
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

                        <strong class="text-link">${isCurrent ? "Currently viewing" : "View Document →"}</strong>

                    </a>
                `;

            })

            .join("");

    }
    else {

      attachments.innerHTML =
        "<p>No related documents.</p>";
    }
  };

  attachments.addEventListener("click", (event) => {
    const link = event.target.closest("[data-document-id]");
    if (!link) return;
    event.preventDefault();
    if (link.dataset.documentId === new URLSearchParams(window.location.search).get("id")) return;
    renderDocument(link.dataset.documentId, true);
    document.querySelector("#document-title").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  window.addEventListener("popstate", () => {
    renderDocument(new URLSearchParams(window.location.search).get("id"));
  });

  renderDocument(params.get("id"));
})();
