# Beaumont Intelligence — Project Status / Handoff

**Updated:** July 27, 2026

## Website / workflow
- Public site: `BeaumontIntelligence.com`, branded Moving Beaumont Forward / Beaumont Intelligence.
- GitHub is the working source repository; `main` is the live/published branch.
- Mobile workflow: edit in GitHub.com, commit to `main`, then verify the live site.
- Cloudflare Access protects the development site. Later: improve mobile login/session duration.
- Current GitHub/deployed files are the source of truth when an older chat conflicts with newer work.

## Site structure
Core navigation: Home, Council Intelligence, Intelligence Centers, Research Library, About.

Intelligence Centers use topic/project subpages, evidence-linked claims, and source registers.

## Existing centers

### Stewart Park
Established reference implementation with timeline, Council records, documents, funding/features/questions, and evidence-certification work. Source-link audit still needs completion.

### Animal Control
Built pages: Overview, Operations, History, Contracts, Municipal Code, Sheltering, Budget & Staffing, Performance, Sources.

Sources page upgraded to direct official records including City Animal Services, budgets, sheltering/service agreements, and Council records.

### Potrero Interchange — COMPLETE
Built pages: Overview, Timeline, Project Design, Funding, Council Actions, Construction, Traffic & Impact, Sources.

- Homepage Potrero quick link opens `potrero-interchange.html`.
- Sources page is now a clickable register using City, RCTC, Council/eScribe, funding, construction, environmental, and concept-plan records.
- Historical lead: March 17, **2015** Council agenda contains a Potrero Interchange Progress Report. Priority research: actual staff report, attachments, and minutes.
- Potrero map idea parked: thumbnail on center → dedicated/full-size viewer. Official concept image uploaded as `potrero-interchange-concept-plan.png`.

### Pennsylvania Avenue Grade Separation — COMPLETE
Treat this as completed work; do not restart from an older draft.

Current framing includes RCTC final-design/right-of-way delivery, June 2027 Ready-to-List target, $49.4M TCEP construction funding, and current City estimate of about $140M. Historical estimates remain dated/distinct.

Known current architecture: Overview, Timeline, Funding & Cost, Project Design, Council Actions, Project Delivery, Construction & Schedule, Questions, Documents, Primary Sources, Evidence Explorer.

## Budget Center — IN PROGRESS
Budget Center work has started and is the active newer center after Potrero and Pennsylvania.

Before continuing in a new chat/device, inspect the current repository files first. The full latest Budget Center page/file state is not reliably captured here, so do not rebuild it from the older Finance/CFD roadmap.

## Source-link standard
Beaumont Intelligence is **Evidence First**.

- Material factual claims should have a visible path to supporting evidence.
- Sources found during research should carry into the published center.
- Source pages should be clickable source registers, not generic lists such as “City budgets” or “engineering reports.”
- Prefer official/primary sources: City records, Council agendas, staff reports, minutes, executed agreements, ordinances/resolutions, budgets/audits, RCTC, WRCOG, Caltrans, CTC, and other government records.
- Supporting news may be used when useful but should be distinguished from primary evidence.
- Distinguish recommendation vs action; agenda item vs adopted action; proposal vs executed agreement; estimate vs grant/award vs contract vs actual expenditure; forecast vs completed milestone; concept plan vs final/as-built design.
- Preserve and date conflicting/evolving official figures instead of hiding the discrepancy.
- If a direct government PDF forces a download on mobile, prefer the official parent meeting/document page when it preserves context and opens better.

## Central Evidence Archive — PLANNED
Build a **separate GitHub repository** and populate it as research proceeds. It should serve Beaumont Intelligence and future unrelated websites/projects.

Suggested repository: `civic-evidence-archive`

```text
civic-evidence-archive/
├── README.md
├── beaumont/
│   └── city-council/
│       └── 2015/
│           ├── 2015-01-06/
│           ├── 2015-01-20/
│           ├── 2015-02-03/
│           ├── 2015-02-17/
│           ├── 2015-03-03/
│           └── 2015-03-17/
├── rctc/
├── wrcog/
├── caltrans/
└── california/
```

Store evidence once and let multiple websites/topics reference it. Metadata should include date, agency, governing body, document type, agenda item, title, topics/tags, original source URL, and verification/source status.

## January–March 2015 Council archive
First evidence-archive collection:
- Jan. 6, 2015
- Jan. 20, 2015
- Feb. 3, 2015
- Feb. 17, 2015
- Mar. 3, 2015
- Mar. 17, 2015

For each meeting, seek: full agenda/packet, staff reports, attachments, minutes, resolutions/contracts where relevant, and original official links.

## Outstanding work
1. Continue **Budget Center** from the current repository state.
2. Create the central evidence-archive repository and README/metadata convention.
3. Reconstruct/archive Jan–Mar 2015 Council records.
4. Investigate the March 17, 2015 Potrero Progress Report + attachments + minutes and feed verified findings into Potrero.
5. Finish source-link audits, especially Stewart Park and any remaining Animal Control/Potrero claim-level links.
6. Later: Potrero concept-map thumbnail → dedicated viewer.
7. Later: improve Cloudflare Access mobile/session UX.
8. Keep Pennsylvania completed unless new evidence requires updates.

## Continuity rule
When conversation length forces a new chat, use this handoff file, then inspect current GitHub files before structural changes. Update this file after major milestones so another chat/device starts from the correct state.
