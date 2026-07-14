# Sprint 2.1 — Data Engine

## Decision

The engine is multi-tenant and workspace-aware from the start, while Stewart Park remains the only seeded project.

## Design principles

- UUID primary keys plus stable archive codes
- normalized source-of-truth tables
- views and FTS projections for read performance
- motions and votes stored separately from agenda recommendations
- funding amounts preserved as dated events
- universal Evidence Explorer links
- public-ready data gated by verification status
- complete database rebuild from source-controlled SQL

## Build order

1. `database/schema.sql`
2. all scripts in `database/seed/`
3. all scripts in `database/views/`
4. `scripts/refresh_search_index.py`
5. `scripts/validate_database.py`

## Commands

```bash
python scripts/build_database.py
python scripts/refresh_search_index.py
python scripts/validate_database.py
```
