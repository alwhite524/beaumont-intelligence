# Dated service-area research completion

Baseline review: October 24, 2026. Visible register: [Service-area actions](service-area-actions.html).

The initial scope is nine selected August–October 2026 Council actions. This is an action-review checklist, not a comprehensive score for a service, the entire website, construction completion, factual certainty, or editorial approval. A later inventory expansion must state its changed denominator rather than imply that earlier scores measured all Council activity.

Each action receives five equally weighted binary checks (20 points each):

1. Dated action and service scope recorded.
2. Decision record and supporting-document route linked. This is discovery credit, not an attachment-completeness audit.
3. Disposition checked against reviewed City minutes. Transcript outcomes retain their evidence limitations and receive no minutes credit.
4. Financial authority classified separately from estimates and expenditure.
5. Final instruments and material discrepancies reconciled. An archived proposed agreement alone does not satisfy this check.

Unverified checks receive zero. Missing checks and the specific next records remain visible. Scores are dated snapshots; they do not automatically improve when a forecast date passes. Cross-listed actions count once in the unique inventory, and service-area counts overlap. No initial record receives final-instrument credit: the executed/corrected records still require collection or review.

The baseline is generated from `data/council/2026-10-20-outcomes.json`, `data/council/recent-center-findings.json`, and the collected August 18 meeting briefing. The generated `data/service-area-actions.json` stores each action, checklist, source routes, limits and follow-up. August 18 records receive no minutes credit because this inventory does not independently establish that review.

Run `python scripts/build_service_area_actions.py` to rebuild the register, its JSON snapshot and navigation. It also runs in the full build. For a new dated review, update the review date, evidence findings, curated selections and checks in the builder together; preserve the prior snapshot in Git. Never promote a check solely to increase a percentage. Use a new dated historical snapshot if comparing scores over time.

Routes are visible in every service-area card, with additional register links on Home and Council Intelligence. Existing project centers, historical evidence and search routes remain available. The initial register does not claim separate coverage for every service topic (for example, solid waste); expand from verified records as those reviews are completed.
