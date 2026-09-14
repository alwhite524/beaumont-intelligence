# WRCOG & Restitution: architecture review and Phase 1

## Repository findings

1. **Framework and routing:** static HTML, CSS, and browser JavaScript in `docs/`; Python builds the SQLite archive and selected generated artifacts. No application-framework router or package.json was found. Centers use flat `.html` paths, so this Center uses `wrcog-restitution.html` and `wrcog-restitution-evidence.html`.
2. **Centers:** `budget.html`, `police.html`, and other Centers use a shared stylesheet, directory cards, overview pages, and sibling evidence/history pages. Dossiers use `dossiers/<subject>/`. Phase 1 creates two pages rather than six empty routes.
3. **Sources:** `data/budget/source-register.json` is explicitly documented as the authoritative financial evidence catalog in `budget/source-register.md`. It uses permanent SRC IDs, official URLs, archive paths, publisher, dates, evidence level, and verification status. Stewart Park also has a project source catalog; the database has document and claim tables. The new Center reuses the financial register without moving or renumbering anything.
4. **Search:** `search.html` loads `search-index.js` and `site-search.js` for browser ranking and filters. `scripts/build_research_library_index.py` builds the separate existing document/transcript discovery index from the storage manifest and meeting records. `scripts/refresh_search_index.py` refreshes SQLite FTS. These are not one unified live index. Phase 1 feeds generated Center/source entries into the existing browser ranking engine; it does not alter the large legacy index or add another search engine.
5. **Evidence components:** static evidence cards, source identifiers, and `viewer.html?url=…` document links are established conventions. The Budget evidence page is hand-maintained HTML, not a live rendering of the JSON register. The new generated view reads the JSON directly.
6. **My Story:** no chapter pages or My Story references were found in the HTML/Markdown content inspected. There is no chapter route to link or migrate. Generic references are scaffolded without inventing Chapter 8 or a narrative quotation.
7. **Minimum change scope:** two generated Center pages, ledger and schema, generic references and schema, a small generator and its generated search feed; integration edits to the directory, search loader, search category handling, and full-build script. This implementation note and focused validation document the contract. No existing source records, entities, or working features are removed.

## Phases

1. **Complete for review:** Center shell, empty ledger/schema, shared Source Register projection, generic evidence-reference schema, directory/site-search integration.
2. Register supplied settlement, audit, judgment, receipt, and other records in the existing financial register. Preserve public documents through the existing official-documents/records and R2 manifest workflow. Verify exact pages and dates before importing financial assertions. Rebuild Research Library after archiving. Extend source indexing with document metadata as records arrive.
3. Load separately supported orders, payments, credits, costs, and allocations. Reconcile totals before presenting Beaumont net recovery. Add recovery-table, settlement, restitution, and timeline pages when supported. Add Recovery, Case, and Timeline Event search entries with real landing anchors.
4. Resolve existing database person/organization IDs; connect actual My Story chapters and passages to evidence. Add Person and My Story Chapter search entries once those records/routes exist. Do not create a parallel entity catalog.

## Data contract

`data/wrcog-restitution/recoveries.json` holds no amounts yet. Every record must include all schema fields; unknown amounts and dates are null, not zero. Amounts are USD. `person_or_entity` will reference the existing database person_id or organization_id, not a new entity system. `case_or_matter` is descriptive until a canonical case model is chosen. `source_ids` resolve exclusively to the existing financial register.

Source acquisition status remains the register's existing vocabulary (Verified, Archived, Pending, Missing, Superseded). Recovery/reference assertion status uses verified-primary, verified-secondary, partially-verified, to-verify, or disputed. Archiving alone never verifies a financial assertion.

Optional additive source fields: `relatedCenters` (stable Center slugs), `relatedStoryChapters` (chapter URLs), `subjects` (existing entity IDs), and `pageReferences` (page labels). To include a registered source here, add `wrcog-restitution` to its `relatedCenters`; retain its existing SRC ID and metadata. Do not create a source record solely to disguise an unsupported research lead as documentary evidence. Deep links resolve as `wrcog-restitution-evidence.html#SRC-…`.

`data/evidence-references.json` supports chapter URL + passage label + typed targets, each with an optional page reference. Target types include source, recovery, center, person, organization, case, and timeline-event. This is a relationship contract, not an implemented My Story website. Referential validation and search for populated chapters/entities are Phase 4 work.

The handoff's approximate judgment exposure, allocation brackets, guarantee, ACFR recovery figure, individual restitution amounts, and personnel/CalPERS assertions remain unverified research leads. None has been loaded as a financial fact. The CalPERS material belongs to related personnel consequences, not the recovery ledger; the service-credit disposition remains unresolved. No external source verification or deployment was performed in Phase 1.

## Rebuild

Run `python scripts/build_wrcog_center.py` (also included in `scripts/build_all.py`). Commit generated HTML and `docs/evidence-search-index.js` with the generator. The source view is static and works without JavaScript. Site search consumes its generated feed through the existing ranking/filter code. The full build also performs unrelated database and publishing work; a focused build is sufficient for this shell.
