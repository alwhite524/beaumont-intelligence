# Private meeting review dashboard

Run from the repository root:

```powershell
.\scripts\start_agenda_workspace.ps1
```

The launcher prefers the bundled Codex Python runtime and falls back to the Python launcher. Alternatively run `python scripts/serve_agenda_workspace.py`. Open `http://127.0.0.1:8765`, then enter the access code printed in that terminal. Use `-Port 8766` with PowerShell or `--port 8766` with Python if needed. The server always binds to loopback; it is not a hosted multi-user application. Keep the server on this computer and do not expose it through a tunnel or public proxy. Stop it with Ctrl+C. Restarting invalidates existing sessions and generates a new access code.

## Complete-draft review workflow

1. In **Upload a complete draft agenda**, enter the meeting date, title and revision label. Select the already prepared complete draft/packet PDF, then any supporting PDFs distributed separately. Staff prepare and correct the source agenda outside this app; the primary workflow is not agenda composition.
2. Choose **Upload and check draft**. Intake reads searchable agenda text, PDF bookmarks and page references. It proposes items and supporting-document ranges, detects unmatched files, checks explicit Attachment A–Z references in detected staff reports, and flags sparse text and repeated content. Limits: 200 MB per PDF, 100 files / 500 MB per intake. Scans have no OCR and receive a manual-review warning.
3. **Confirm detected agenda and attachment matches**. Open each range, correct item associations using the dropdown, and tick its confirmation. Acknowledge the inventory before **Save as new draft revision**. Unmatched documents may remain unmatched, but stay visible as open issues. Intake is staged: failure or cancellation before confirmation leaves the active draft untouched. Files and stages are retained privately, not published.
4. Review the source documents and save private notes. Record content, cost, date, contractual or attachment concerns under **Issues and correction rechecks**. Automated checks are structural aids, not a legal/financial audit or assurance of all attachment content.
5. Staff correct the package in their existing authoring tools. Upload the complete corrected draft using the **same meeting date**. Provide the complete set of separately supplied attachments again, not only changed files. Confirm the new inventory; it becomes the next numbered revision.
6. The revision comparison lists added, removed, changed and unchanged sources. Source fingerprints include PDF page content and image resources, not just extracted text. Conservative changes may require another visual check. Earlier draft files, findings, resolutions and notes remain available through the revision selector. Earlier revisions are read-only.
7. Prior issues carry forward as **needs-recheck**, including previously resolved issues and issues whose automated trigger has disappeared. The app never interprets a new upload or a changed fingerprint as proof of correction. Resolve each issue with an explanation and a supporting document/page in the current revision, or keep it open with a note. Initial findings and earlier resolution history remain visible.
8. Private notes carry forward; document checkmarks and ready status reset on a new revision. Review and check supporting documents again. An item cannot be marked ready while its findings or meeting-wide issues remain open, or supporting documents remain unchecked. “Ready for editorial review” remains a staff judgment, separate from agenda approval, publication, payment or completed work.
9. Export the selected revision's saved review as JSON for a deliberate handoff. Save notes before exporting. JSON exports contain metadata/findings/notes, not PDF bytes; back up the whole private-workspace folder for source files too.

Partial/uncertain extraction is never called complete. Bookmarked packages produce individual attachment ranges. Without bookmarks, agenda page references can locate item sections, with an explicit finding that individual attachment boundaries/completeness still need manual review. If no numbered structure can be read, the full packet remains available with unresolved extraction findings; use a searchable/bookmarked PDF for a reliable automatic inventory. Item association confirmation is a review step, not editing or composing the source agenda.

The existing collected agendas are still available as reference records. New draft revisions are isolated from those published records. Old manual-upload inventories remain readable; manual agenda-building is no longer shown as the primary interface.

## Privacy and storage

UI files live in `private-dashboard/`, outside the published `docs/` tree. Private reviews save atomically to `private-workspace/agenda-reviews/YYYY-MM-DD.json`, which Git ignores. User-created meeting/item inventories live in `private-workspace/meetings/`; uploaded PDFs live in `private-workspace/documents/` using checksum-based filenames rather than supplied paths. They are never written into public HTML, Council source JSON or the public database. This folder is under the repository's filesystem location; if the repository is in OneDrive or another synced folder, its private workspace may also sync through that service. Exports go to the browser's download location and should be handled as private files. JSON exports include review and source metadata, not PDF bytes; back up the entire private-workspace folder to preserve uploaded files as well.

The local server requires an access-code session for meeting data, reference documents, saves and exports. Session cookies are HttpOnly and SameSite=Strict. Mutations require the exact local Origin, and Host validation blocks arbitrary hostnames. The access code is not placed in a URL, browser storage or Git. Private notes are rendered as text, not HTML. There is no external AI or transmission of private notes to an external service. Opening an official/public PDF still contacts its source host; the server sends a no-referrer policy and notes are not included in document URLs.

Locally collected PDFs use a page-by-page renderer through authenticated `/document` and `/api/document-page` routes when `pypdfium2` is available (it is included in the bundled runtime). The local viewer has previous/next and page-jump controls. Raster pages preserve the source appearance but are not selectable text; the original PDF link remains available. Missing local PDFs fall back to the existing viewer through authenticated `/reference/` routes. External document availability/CORS still depends on the source host. The server does not proxy arbitrary URLs. Loopback access controls do not encrypt files at rest or protect against someone with access to your Windows account.

Draft packages and revision manifests live in `private-workspace/packages/`; staged uploads live in `private-workspace/intake/`. Per-revision notes are in `private-workspace/agenda-reviews/YYYY-MM-DD-rN.json`.

The meeting picker combines structured `data/council/YYYY-MM-DD-agenda.json` meetings with user-created private meetings. The loader joins packet maps, existing source JavaScript, document-review findings and item-level outcomes where available; it does not invent missing decisions. Private uploads can supplement existing meetings without changing their official inventories. Document and flag identities are hashed from their source content to avoid silently applying old review checks to changed records.

PDF upload parsing requires `pypdf`; local page rendering uses `pypdfium2` and Pillow. All three are available in the bundled runtime used by the PowerShell launcher. Other file formats are not currently accepted. The dashboard remains a local application; a remotely hosted, multi-user deployment would still require a separate authentication and private-storage deployment.

## Verification

```text
python -m unittest discover -s tests -p test_private_agenda_workspace.py
python -m unittest discover -s tests -p test_agenda_package_workflow.py
node --check private-dashboard/dashboard.js
node --check private-dashboard/package-review.js
```

The dashboard is deliberately excluded from public-site builds and navigation. No publishing, remote account system or live collaboration has been added.
