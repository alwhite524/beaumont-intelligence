# Sprint 2.2 — Stewart Park Import

## Delivered

- Canonical CSV/JSON dataset for Stewart Park
- Repeatable import pipeline
- Full database build orchestration
- Stewart Park-specific quality checks
- Search-index refresh
- Imported meetings, agenda items, sources, organizations, features, funding, media, verified questions, and evidence links

## Counts

```json
{
  "project": 1,
  "meeting": 13,
  "agenda_item": 15,
  "document": 10,
  "organization": 5,
  "project_feature": 13,
  "funding_event": 2,
  "media": 2,
  "verified_question": 4,
  "evidence_link": 6,
  "search_index": 30
}
```

## Commands

```bash
python scripts/build_all.py
```

## Important limitation

Council motions, votes, minutes links, and video timestamps remain unpopulated until directly verified from the official record.
