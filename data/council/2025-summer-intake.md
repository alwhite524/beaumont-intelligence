# Summer 2025 Council archive intake

Processed October 10, 2026 from the four user-supplied agenda packages.

| Meeting | Packet pages | Numbered items | Supporting PDFs |
| --- | ---: | ---: | ---: |
| June 3, 2025 | 1,702 | 40 | 124 |
| June 17, 2025 | 2,788 | 35 | 100 |
| July 15, 2025 | 2,369 | 38 | 99 |
| August 19, 2025 | 3,058 | 47 | 130 |
| Total | 9,917 | 160 | 453 |

All 453 attachments were matched by item and normalized filename against the official City HTML agenda and supplied packet bookmarks. The agenda JSON retains original City URLs and packet page boundaries. Including four agenda extracts and four full packets, 461 PDFs are archived in Cloudflare R2. Each public URL returned a PDF signature and the production BI origin CORS header. PDF files and temporary extraction files remain ignored by Git.

Interactive agendas use the embedded BI document viewer. Local browser testing verified search, expanded outcomes, and the document modal route. Localhost is not an allowed R2 viewer origin; production-origin compatibility was verified separately by HTTP headers. Sample agenda pages were rendered and visually inspected.

YouTube automatic captions refreshed June 3 and August 19 transcripts and supplied the new June 17 transcript. July 15 offered no captions; its existing AI transcript was retained with normalized reader timestamps. Machine-generated names, figures, quotations, and approximate discussion timestamps require recording verification.

Official minutes supply outcomes separately from recommendations. Review notes retain the July 15 consent-range inconsistency, August 19 combined motions and corrected three-year tree-service term, missing vote tallies, and ambiguous source dates or figures. Pennsylvania Avenue widening and grade separation remain distinct projects.

Added 22 center findings and refreshed three existing findings. Rebuilt relevant center detail pages, seven landing pages, service-area evidence groups, the meeting catalog, and the Research Library (3,364 records).

Validation passed: nine Python tests covering historical archive coverage, VTT conversion, and this batch; three Node test files covering meeting-page rendering, Research Library search, and minutes links. R2 sync also verified the four pre-existing minutes PDFs (465 objects checked in total).

Rebuild order: `build_2022_interactive_agendas.py`, `build_recent_center_findings.py`, `build_center_archive_updates.py`, `build_council_meeting_sources.py`, then `build_research_library_index.py`. Run these from the repository root with Python. The historical renderer filename is retained for compatibility and now supports reviewed 2025 meetings.

R2 uploads are complete. Website changes require the user's normal commit and deployment workflow.
