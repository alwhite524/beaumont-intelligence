# Beaumont Intelligence

Version **0.8.0** — Sprint 2.1 Data Engine

Beaumont Intelligence is a source-first, searchable research and civic-intelligence platform. It is the private source of truth for evidence, analysis, verification, and editorial preparation. Approved public material is published separately to Moving Beaumont Forward.

See [`docs/platform-architecture.md`](docs/platform-architecture.md) for the center, dossier, and publishing model.

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

## PD Technology publishing

The editable Beaumont Intelligence source for the PD Technology article is
`data/police/pd-technology.html`. Publish it into the existing Moving Beaumont
Forward design with `python scripts/publish_pd_technology.py`; use `--check` to
verify that the public copy is current without writing files.

## Transcript verification workflow

When a Council transcript is added, review the meeting against the entire site—not only the center that prompted the upload. Match every relevant agenda item to all applicable Intelligence Centers, add timestamped video links and verified outcomes, update source datasets and generated site data, and refresh the search index. A transcript should remain unattached when the corresponding meeting contains no relevant item for a center.

## Web preview

Open `docs/index.html` or run:

```bash
python scripts/serve_web.py
```

## Document storage

Large public PDFs are synchronized to the Cloudflare R2 bucket
`beaumont-intelligence-documents` and served from
`https://documents.beaumontintelligence.com`. Credentials belong in the
git-ignored `.r2.local.json` file.

Place a new PDF under its intended `docs/official-documents` or
`docs/records/agenda-packets` path, run the sync, verify the manifest, and then
remove the local copy. PDFs in those folders are ignored to prevent accidental
commits.

```bash
python -m pip install -r requirements-r2.txt
python scripts/sync_r2_documents.py
python scripts/sync_r2_documents.py --verify-manifest
```

## Application routes
- `docs/index.html` — Beaumont Intelligence landing page
- `docs/intelligence-centers.html` — Intelligence Center directory
- `docs/stewart-park.html` — Stewart Park Intelligence Center
- `docs/pennsylvania-grade-separation.html` — Pennsylvania Avenue Grade Separation Intelligence Center
- `docs/police.html` — Police Intelligence Center
- `docs/dossiers/police/flock-cameras.html` — Flock Camera research dossier

See `docs/github-project-board.md`.
