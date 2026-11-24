# Dated service-area research completion

Baseline review: October 24, 2026. Latest review: November 23, 2026. [Service-area actions register](service-area-actions.html).

All nine tracked actions completed all five checks. These include three August 18 actions, one October 6 action, and five October 20 actions. The register lists actions with open checks and is currently empty.

The initial scope is nine selected August–October 2026 Council actions. This is an action-review checklist, not a comprehensive score for a service, the entire website, construction completion, factual certainty, or editorial approval. A later inventory expansion must state its changed denominator rather than imply that earlier scores measured all Council activity.

Each action receives five equally weighted binary checks (20 points each):

1. Dated action and service scope recorded.
2. Decision record and supporting-document route linked. This is discovery credit, not an attachment-completeness audit.
3. Disposition checked against reviewed City minutes. Transcript outcomes retain their evidence limitations and receive no minutes credit.
4. Financial authority classified separately from estimates and expenditure.
5. Final instruments and material discrepancies reconciled. An archived proposed agreement alone does not satisfy this check.

Unverified checks receive zero. For actions under review, the register shows missing checks and the next records needed. Scores reflect evidence reviewed on the stated date. Cross-listed actions count once in the unique inventory, and service-area counts overlap.

The review uses the October 20 outcomes, the October 6 minutes findings, and the August 18 briefing and supplied minutes. The reviewer confirmed reconciliation of final instruments and material discrepancies for all three meetings. The register builder retains the completed checks. The generated `data/service-area-actions.json` contains the checklist, sources, and follow-up for actions still under review.

Run `python scripts/build_service_area_actions.py` to rebuild the register, its JSON snapshot and navigation. It also runs in the full build. For a new dated review, update the review date, evidence findings, curated selections and checks in the builder together; preserve the prior snapshot in Git. Never promote a check solely to increase a percentage. Use a new dated historical snapshot if comparing scores over time.

When actions have open checks, the builder adds register links to the relevant Intelligence Center cards and the landing pages. The underlying Council meeting records remain available through Council Intelligence.
