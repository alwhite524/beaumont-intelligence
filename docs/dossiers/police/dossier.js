(() => {
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
