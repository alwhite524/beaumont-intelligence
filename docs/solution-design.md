# Solution Design Document

## Purpose
The Beaumont Project Library is a searchable, source-first archive of major City of Beaumont projects. Stewart Park is the pilot.

## Initial scope
- Council meetings and agenda items
- Staff reports, minutes, packets, contracts, presentations, and news releases
- Official project pages
- Videos and timestamps
- Renderings and photographs
- Grants, funding actions, organizations, and project features
- Factual claims and supporting evidence

## Architecture
### Source layer
Official URLs and optionally archived copies of public records.

### Metadata layer
SQLite stores normalized entities and junction tables. Stable archive identifiers supplement UUID primary keys.

### Search layer
SQLite FTS5 indexes titles, summaries, keywords, and extracted text. A static JSON index will later support GitHub Pages.

### Presentation layer
A mobile-first static site will provide project pages, filters, timelines, source cards, renderings, FAQs, and direct links.

## Modeling strategy
Normalize the core. Selectively denormalize search and reporting projections.

## Evidence levels
- A — official agenda, minutes, staff report, contract, resolution, ordinance, or government record
- B — official City or agency project page, presentation, or news release
- C — credible secondary publication or agency partner material
- D — campaign, social-media, photograph, or other supporting material

## Verification states
- unreviewed
- reviewed
- verified
- disputed
- superseded

No timestamp is public-ready until verified.

## Publication pipeline
1. Add or import a source.
2. Assign archive ID and evidence level.
3. Link projects, meetings, agenda items, organizations, topics, and media.
4. Add factual claims only when traceable to evidence.
5. Review and verify.
6. Generate public JSON and static pages.
7. Publish through GitHub Pages.

## Roadmap
- 0.1 schema, standards, source seed catalog
- 0.2 complete Stewart Park meeting and document inventory
- 0.3 verified video timestamps and Council actions
- 0.4 rendering and media archive
- 0.5 searchable static website
- 0.9 editorial and link QA
- 1.0 public Stewart Park archive
