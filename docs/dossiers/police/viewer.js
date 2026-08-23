(() => {
  const sourceId = new URLSearchParams(window.location.search).get("doc");
  const sources = {
    "flock-2023-staff-report": { title: "Flock Group Inc. Encroachment Agreement — Staff Report", description: "City staff report documenting the 2020 Sundance arrangement and the proposed citywide right-of-way agreement.", type: "Official staff report · PDF", date: "May 2, 2023", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2023-05-02/d-7-staff-report-flock-encroachment-agreement.pdf" },
    "flock-2024-staff-report": { title: "Flock Safety Camera Expansion — Staff Report", description: "City staff report supporting the two-year service contract for 36 additional Flock cameras.", type: "Official staff report · PDF", date: "August 20, 2024", format: "pdf", url: "https://pub-beaumont.escribemeetings.com/FileStream.ashx?DocumentId=4811" },
    "axon-2025-staff-report": { title: "Axon Body-Worn Cameras and Software — Staff Report", description: "City staff report supporting the five-year Axon body-worn-camera and associated-software agreement.", type: "Official staff report · PDF", date: "December 2, 2025", format: "pdf", url: "https://pub-beaumont.escribemeetings.com/FileStream.ashx?DocumentId=8336" },
    "drone-2026-staff-report": { title: "Drone-as-First-Responder Program — Staff Report", description: "City staff report supporting the three-year Flock Safety Drone-as-First-Responder agreement.", type: "Official staff report · PDF", date: "April 7, 2026", format: "pdf", url: "https://pub-beaumont.escribemeetings.com/FileStream.ashx?DocumentId=9702" },
    "peregrine-2026-agenda-package": { title: "August 4, 2026 City Council Agenda Package", description: "Official City agenda package containing the Peregrine platform record considered as Agenda Item G.14.", type: "Official agenda package · PDF", date: "August 4, 2026", format: "pdf", url: "https://pub-beaumont.escribemeetings.com/FileStream.ashx?DocumentId=10591" }
  };
  const record = sources[sourceId];
  const title = document.querySelector("#source-title");
  const description = document.querySelector("#source-description");
  const type = document.querySelector("#source-type");
  const date = document.querySelector("#source-date");
  const content = document.querySelector("#source-content");
  const showError = (message) => { content.innerHTML = `<p class="pdf-error">${message}</p>`; };
  const renderPdf = async () => {
    try {
      const pdfjsLib = await import("https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.min.mjs");
      pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.worker.min.mjs";
      const pdf = await pdfjsLib.getDocument({ url: record.url }).promise;
      content.replaceChildren();
      for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
        const page = await pdf.getPage(pageNumber);
        const baseViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.max(content.clientWidth - 24, 280);
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
        canvas.setAttribute("aria-label", `${record.title}, page ${pageNumber} of ${pdf.numPages}`);
        content.appendChild(canvas);
        await page.render({ canvasContext: context, viewport }).promise;
      }
    } catch (error) {
      showError("The PDF could not be displayed. Please return to the dossier and try again.");
      console.error("Unable to render PDF", error);
    }
  };
  if (!record) {
    title.textContent = "Source not found";
    description.textContent = "The requested source is not part of this dossier.";
    showError("No source was selected.");
    return;
  }
  document.title = `${record.title} | Moving Beaumont Forward`;
  title.textContent = record.title;
  description.textContent = record.description;
  type.textContent = record.type;
  date.textContent = record.date;
  renderPdf();
})();
