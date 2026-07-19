(() => {
  const params = new URLSearchParams(window.location.search);
  const documentId = params.get("id");

  const title = document.querySelector("#document-title");
  const summary = document.querySelector("#document-summary");
  const meetingDate = document.querySelector("#meeting-date");
  const agendaItem = document.querySelector("#agenda-item");
  const category = document.querySelector("#category");
  const documentType = document.querySelector("#document-type");
  const attachments = document.querySelector("#attachments");
  const relatedIntelligence = document.querySelector("#related-intelligence");
  const briefingLink = document.querySelector("#briefing-link");
  const pdfLink = document.querySelector("#pdf-link");

  const record = documentLibrary.find(
    (item) => item.id === documentId
  );

  if (!record) {
    title.textContent = "Document not found";
    summary.textContent =
      "The requested document could not be found in the Official Source Library.";

    attachments.innerHTML =
      '<p><a href="index.html">Return to the Official Source Library →</a></p>';

    relatedIntelligence.innerHTML = "";
    briefingLink.hidden = true;
    pdfLink.hidden = true;

    return;
  }

  document.title =
    `${record.title} | Beaumont Intelligence`;

  title.textContent = record.title;
  summary.textContent = record.summary;

  meetingDate.textContent = record.meetingLabel;
  agendaItem.textContent = record.agendaItem;
  category.textContent = record.category;
  documentType.textContent = record.documentType;

  briefingLink.href = record.briefing;
  pdfLink.href = record.pdf;
  pdfLink.target = "_blank";
  pdfLink.rel = "noopener";

 if (record.relatedDocuments?.length) {

    attachments.innerHTML =
        record.relatedDocuments
            .map(id => {

                const related =
                    documentLibrary.find(
                        d => d.id === id
                    );

                if (!related) return "";

                return `
                    <article class="card">

                        <div class="meta">

                            ${related.documentType}

                        </div>

                        <h3>

                            ${related.title}

                        </h3>

                        <p>

                            ${related.summary}

                        </p>

                        <a
                            class="text-link"
                            href="viewer.html?id=${related.id}">

                            View Document →

                        </a>

                    </article>
                `;

            })

            .join("");

}
else {

    attachments.innerHTML =
        "<p>No related documents.</p>";

}

  if (record.relatedIntelligence?.length) {
    relatedIntelligence.innerHTML = record.relatedIntelligence
      .map(
        (item) => `
          <a class="text-link" href="${item.url}">
            ${item.title} →
          </a>
        `
      )
      .join("<br>");
  } else {
    relatedIntelligence.innerHTML =
      "<p>No related Intelligence Centers are currently linked.</p>";
  }
})();