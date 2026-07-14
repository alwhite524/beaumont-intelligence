# Changelog

## 0.7.0 — Sprint 2.3 Public Web Application
- Added a mobile-first Stewart Park Intelligence Center.
- Added project metrics, timeline, features, funding, Council records, verified questions, and source library.
- Added evidence expansion for resident questions.
- Added static data export suitable for GitHub Pages.
- Added local preview server.
- Preserved unverified motions, votes, minutes, and timestamps as incomplete.

## 0.6.0 — Sprint 2.2 Stewart Park Import

- Added canonical Stewart Park CSV/JSON datasets.
- Added repeatable Stewart Park importer.
- Added full build orchestration.
- Imported meetings, agenda items, sources, organizations, features, funding events, media, verified questions, and evidence links.
- Added Stewart Park-specific quality checks.
- Refreshed FTS5 search index from imported production data.
- Preserved motions, votes, minutes links, and video timestamps as unverified/empty.

## 0.5.0 — Sprint 2.1 Data Engine

- Rebuilt the schema around tenant, workspace, project, phase, and feature entities.
- Added exact Council action and video-segment models.
- Added contracts, amendments, organizations, people, funding sources, and funding events.
- Added verified questions, claims, and a universal Evidence Explorer.
- Added topic tagging, source audits, research tasks, and FTS5 search.
- Added reusable views for dashboards, Council actions, evidence, and verification queues.
- Added deterministic build, search refresh, validation, and quality-check scripts.
- Seeded MBF, the 2026 campaign workspace, Stewart Park, and its two phases.
