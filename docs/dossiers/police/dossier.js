(() => {
  document.querySelectorAll('a[href^="../../"]').forEach((link) => {
    if (["../../index.html", "../../police.html", "../../briefings/2026-08-04.html"].includes(link.getAttribute("href"))) return;
    link.remove();
  });

  const sourceRegister = document.querySelector(".source-register");
  const peregrineSource = [...(sourceRegister?.children || [])].find((item) => item.textContent.includes("Peregrine platform"));
  if (sourceRegister && peregrineSource && !sourceRegister.querySelector('[data-source="prepared-ai"]')) {
    const preparedSource = document.createElement("li");
    preparedSource.dataset.source = "prepared-ai";
    preparedSource.innerHTML = '<strong>Prepared AI dispatch:</strong> <a href="viewer.html?doc=prepared-ai-2026-staff-report">June 16, 2026 staff report · PDF →</a> and <a href="video-viewer.html?segment=prepared-ai">bounded video segment →</a>';
    sourceRegister.insertBefore(preparedSource, peregrineSource);
  }

  const cards = [...document.querySelectorAll(".technology-card-stack > .dossier-technology-card")];
  if (!cards.length) return;

  cards.forEach((card) => {
    const accordion = card.querySelector(".accordion");
    const sourceHeading = card.querySelector(".official-documents-heading");

    if (accordion && sourceHeading) {
      const sourcePanel = document.createElement("details");
      sourcePanel.className = "source-verification-panel";
      const sourceSummary = document.createElement("summary");
      sourceSummary.textContent = "Verify record and open sources";
      const sourceBody = document.createElement("div");
      let node = sourceHeading.nextSibling;
      sourceHeading.remove();
      while (node) {
        const next = node.nextSibling;
        sourceBody.appendChild(node);
        node = next;
      }
      sourcePanel.append(sourceSummary, sourceBody);
      accordion.appendChild(sourcePanel);
    }

    card.querySelectorAll(".accordion > details").forEach((panel) => {
      panel.removeAttribute("open");
    });

    card.addEventListener("toggle", () => {
      if (!card.open) return;
      cards.forEach((other) => {
        if (other !== card) other.removeAttribute("open");
      });
    });
  });
})();
