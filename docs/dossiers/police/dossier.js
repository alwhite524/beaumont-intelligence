(() => {
  const cards = [...document.querySelectorAll(".technology-card-stack > .agenda-item")];
  if (!cards.length) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const animate = (element, opening) => {
    if (reduceMotion) return;
    element.animate(
      opening
        ? [{ opacity: 0, transform: "translateY(-8px)" }, { opacity: 1, transform: "translateY(0)" }]
        : [{ opacity: 1, transform: "translateY(0)" }, { opacity: 0, transform: "translateY(-6px)" }],
      { duration: opening ? 260 : 180, easing: "cubic-bezier(.2,.8,.2,1)" }
    );
  };

  const setCard = (card, open, moveFocus = false) => {
    const button = card.querySelector(".dossier-card-toggle");
    const content = card.querySelector(".dossier-card-content");
    if (!button || !content || card.classList.contains("is-open") === open) return;
    if (!open) card.querySelectorAll("details[open]").forEach((detail) => detail.removeAttribute("open"));
    animate(content, open);
    card.classList.toggle("is-open", open);
    button.setAttribute("aria-expanded", String(open));
    button.querySelector(".toggle-state").textContent = open ? "Collapse" : "Open dossier";
    if (moveFocus) button.focus({ preventScroll: true });
  };

  cards.forEach((card, index) => {
    const body = card.querySelector(".agenda-item-body");
    const heading = body?.querySelector(":scope > h3");
    if (!body || !heading) return;

    const content = document.createElement("div");
    content.className = "dossier-card-content";
    content.id = `technology-card-content-${index + 1}`;
    while (heading.nextSibling) content.appendChild(heading.nextSibling);
    body.appendChild(content);

    const sourceHeading = content.querySelector(":scope > .official-documents-heading");
    const accordion = content.querySelector(":scope > .accordion");
    if (sourceHeading && accordion) {
      const sourcePanel = document.createElement("details");
      sourcePanel.className = "source-verification-panel";
      const sourceSummary = document.createElement("summary");
      sourceSummary.textContent = "Verify record and open sources";
      const sourceBody = document.createElement("div");
      let sourceNode = sourceHeading.nextSibling;
      sourceHeading.remove();
      while (sourceNode) {
        const next = sourceNode.nextSibling;
        sourceBody.appendChild(sourceNode);
        sourceNode = next;
      }
      sourcePanel.append(sourceSummary, sourceBody);
      accordion.appendChild(sourcePanel);
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "dossier-card-toggle";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", content.id);
    button.innerHTML = `<span>${heading.textContent}</span><small class="toggle-state">Open dossier</small><i aria-hidden="true"></i>`;
    heading.textContent = "";
    heading.appendChild(button);

    card.querySelectorAll("details").forEach((detail) => {
      detail.removeAttribute("open");
      detail.addEventListener("toggle", () => {
        if (!detail.open) return;
        card.querySelectorAll("details[open]").forEach((other) => {
          if (other !== detail) other.removeAttribute("open");
        });
      });
    });

    button.addEventListener("click", () => {
      const willOpen = !card.classList.contains("is-open");
      if (willOpen) cards.forEach((other) => { if (other !== card) setCard(other, false); });
      setCard(card, willOpen);
    });
  });
})();
