# Council minutes

Keep all standalone minutes PDFs and annual minutes compilations in this folder.
PDFs are preserved in the public document archive and excluded from Git, consistent
with the repository's other public records. The tracked catalog is
`data/council/minutes-register.json`; it includes local locations, stable archive
URLs, checksums, meeting dates and extracted searchable text.

For future intake:

1. Preserve the original PDF here and register/upload it using the existing
   `data/document-storage-manifest.json` and `scripts/sync_r2_documents.py` workflow.
   Existing archived files retain their original object keys and URLs.
2. Run `scripts/build_minutes_register.py` (requires pypdf). For a new filename
   pattern, explicitly establish the meeting date from the minutes before adding
   its mapping. An approval agenda's date is not the date of the minutes.
3. Run `scripts/build_council_meeting_sources.py` and
   `scripts/build_research_library_index.py` to refresh meeting links and search.
4. Verify dates, links and search results. Scanned pages without extractable text
   remain readable PDFs but require OCR before their contents can be searched.

Annual compilations do not imply complete coverage. Only page-reviewed meeting
references should link an annual compilation to a specific meeting. Search text
is a discovery aid; substantive claims still require the existing Source Register.
