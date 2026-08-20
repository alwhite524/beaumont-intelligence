(() => {
  const sourceId = new URLSearchParams(window.location.search).get("doc");
  const sources = {
    "flock-2023-staff-report": { title: "Flock Group Inc. Encroachment Agreement — Staff Report", description: "City staff report documenting the 2020 Sundance arrangement and the proposed citywide right-of-way agreement.", type: "Official staff report · PDF", date: "May 2, 2023", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2023-05-02/d-7-staff-report-flock-encroachment-agreement.pdf" },
    "transcript-2022-04-05": { title: "City Council Meeting Transcript", description: "Transcript containing the April 2022 legislative discussion of proposed ALPR retention limits.", type: "Meeting transcript · Text", date: "April 5, 2022", format: "text", url: "../../transcripts/2022-04-05-city-council-transcript.txt" },
    "transcript-2023-05-02": { title: "City Council Meeting Transcript", description: "Transcript for the meeting at which the citywide Flock encroachment agreement passed with the consent calendar.", type: "Meeting transcript · Text", date: "May 2, 2023", format: "text", url: "../../transcripts/2023-05-02-city-council-transcript.txt" },
    "transcript-2024-08-20": { title: "City Council Meeting Transcript", description: "Transcript of the discussion and approval of the 36-camera Flock expansion.", type: "Meeting transcript · Text", date: "August 20, 2024", format: "text", url: "../../transcripts/2024-08-20-city-council-transcript.txt" }
  };
  const record = sources[sourceId];
  const title = document.querySelector("#source-title");
  const description = document.querySelector("#source-description");
  const type = document.querySelector("#source-type");
  const date = document.querySelector("#source-date");
  const content = document.querySelector("#source-content");
  const showError = (message) => { content.innerHTML = `<p class="pdf-error">${message}</p>`; };
  const renderText = async () => {
    try {
      const response = await fetch(record.url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const pre = document.createElement("pre");
      pre.className = "dossier-transcript";
      pre.textContent = await response.text();
      content.replaceChildren(pre);
    } catch (error) {
      showError("The transcript could not be displayed. Please return to the dossier and try again.");
      console.error("Unable to render transcript", error);
    }
  };
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
  if (record.format === "pdf") renderPdf(); else renderText();
})();
