(() => {
  const sourceId = new URLSearchParams(window.location.search).get("doc");
  const sources = {
    "flock-2023-staff-report": { title: "Flock Group Inc. Encroachment Agreement — Staff Report", description: "City staff report documenting the 2020 Sundance arrangement and the proposed citywide right-of-way agreement.", type: "Official staff report · PDF", date: "May 2, 2023", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2023-05-02/d-7-staff-report-flock-encroachment-agreement.pdf" },
    "flock-2024-staff-report": { title: "Flock Safety Camera Expansion — Staff Report", description: "City staff report supporting the two-year service contract for 36 additional Flock cameras.", type: "Official staff report · PDF", date: "August 20, 2024", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2024-08-20/j-5-staff-report-flock-camera-expansion.pdf" },
    "axon-2025-staff-report": { title: "Axon Body-Worn Cameras and Software — Staff Report", description: "City staff report supporting the five-year Axon body-worn-camera and associated-software agreement.", type: "Official staff report · PDF", date: "December 2, 2025", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2025-12-02/j-4-staff-report-axon-technology-agreement.pdf" },
    "drone-2026-staff-report": { title: "Drone-as-First-Responder Program — Staff Report", description: "City staff report supporting the three-year Flock Safety Drone-as-First-Responder agreement.", type: "Official staff report · PDF", date: "April 7, 2026", format: "pdf", url: "https://documents.beaumontintelligence.com/official-documents/2026-04-07/j-9-staff-report-drone-as-first-responder.pdf" },
    "prepared-ai-2026-staff-report": { title: "Axon Prepared AI Dispatch Software — Staff Report", description: "Official City staff report supporting the Axon Prepared AI dispatch-software service agreement considered as Consent Item G.13.", type: "Official staff report · PDF", date: "June 16, 2026", format: "pdf", url: "https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId=10275" }
  };
  const record = sources[sourceId];
  const title = document.querySelector("#source-title");
  const description = document.querySelector("#source-description");
  const type = document.querySelector("#source-type");
  const date = document.querySelector("#source-date");
  const content = document.querySelector("#source-content");
  const showError = (message) => { content.innerHTML = `<p class="pdf-error">${message}</p>`; };
  const renderPdf = () => window.BIPdfReader.open(content, record.url, record.title, record);
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
