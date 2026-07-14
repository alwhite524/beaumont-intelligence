# MBF Digital Knowledge Base

Version **0.7.0** — Sprint 2.1 Data Engine

The Move Beaumont Forward Digital Knowledge Base is a source-first, searchable project intelligence platform. Stewart Park is the first seeded project.

## Build

```bash
python scripts/build_database.py
python scripts/refresh_search_index.py
python scripts/validate_database.py
```

## Core capabilities

- multi-tenant / multi-workspace model
- reusable projects and phases
- meetings, agenda items, motions, votes, and video segments
- documents, renderings, contracts, funding events, and organizations
- verified resident questions and atomic claims
- universal Evidence Explorer
- SQLite FTS5 search
- complete rebuild from source-controlled SQL

See `docs/sprint-2.1-data-engine.md` and `docs/data-engine-dictionary.md`.

## Full build

```bash
python scripts/build_all.py
```

## Web preview

Open `website/index.html` or run:

```bash
python scripts/serve_web.py
```
