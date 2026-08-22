# Beaumont Intelligence publishing architecture

## Purpose

Beaumont Intelligence is the private research and civic-intelligence workspace. It is the source of truth for evidence collection, analysis, unresolved questions, internal status, and editorial preparation.

Moving Beaumont Forward is the public publishing site. Content reaches it only after the research record is verified and approved for publication. The two systems serve different audiences and should not be treated as mirrors.

## Publishing workflow

Every publishable body of work moves through these stages:

1. **Research** — collect records, meeting history, resident questions, and leads.
2. **Evidence** — attach primary sources and distinguish facts from assertions.
3. **Analysis** — explain what the record establishes, conflicts, and leaves unanswered.
4. **Verify** — check dates, figures, votes, links, quotations, and material claims.
5. **Editorial review** — decide what is suitable for a public audience and remove private working material.
6. **Publish** — intentionally transfer the approved version to Moving Beaumont Forward.

Publication is a deliberate editorial action, not an automatic synchronization. A dossier may remain private indefinitely, and individual internal notes or records may never be published.

### PD Technology integration

The canonical, editable PD Technology article is `data/police/pd-technology.html`. Its Moving Beaumont Forward artifact is `docs/dossiers/police/flock-cameras.html`. Run `python scripts/publish_pd_technology.py` to publish the source without transforming its established MBF design, or add `--check` to detect drift without changing either file.

## Center and dossier model

An Intelligence Center is an index for a subject area. It helps researchers and readers locate distinct dossiers and supporting center-wide material; it should not become a single oversized investigation.

A dossier is the source-of-truth record for one defined issue. Police-related dossiers use the route pattern:

`docs/dossiers/police/<dossier-name>.html`

Each dossier should contain:

- executive summary;
- research and publication status;
- key questions;
- verified timeline;
- costs and financial gaps;
- Council actions;
- documents and video evidence;
- analysis that distinguishes facts, inferences, and open questions;
- frequently asked questions;
- primary sources;
- records still needed; and
- last-updated date.

The reusable starting file is `templates/dossier-template.html`.

## Status language

Research status and publication status are separate:

- **Research active** — material is still being collected or reconciled.
- **Evidence assembled** — the core source set is present but verification may continue.
- **Verified** — material claims have been checked against primary sources.
- **Editorial review** — a public version is being evaluated and prepared.
- **Ready to publish** — editorial approval is complete.
- **Published** — an approved public version exists on Moving Beaumont Forward.

A completion percentage describes research readiness, not factual certainty and not permission to publish. Every dossier must state what remains before it can advance.

## First implementation: Flock cameras

The Police Intelligence Center is the index. The Flock Camera dossier is the first standalone police dossier and owns the fixed-camera ALPR research previously distributed across Police History, Operations, Questions, and Evidence.

The Flock Drone-as-First-Responder program is a separate technology and should not be merged into the fixed-camera ALPR dossier. It may become its own dossier later.
