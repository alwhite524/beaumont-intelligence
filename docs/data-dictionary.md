# Data Dictionary

- `project`: one record per capital project or initiative.
- `meeting`: one public meeting; meeting and video URLs are separate.
- `agenda_item`: a substantive item; timestamps are seconds from the official video.
- `document`: an official or secondary source with evidence and verification metadata.
- `project_document`: many-to-many project/document link.
- `agenda_item_document`: links staff reports and attachments to agenda items.
- `organization`: City departments, consultants, contractors, and agencies.
- `topic`: controlled vocabulary such as ORLP, NEPA, splash pad, pickleball, and phasing.
- `media`: renderings, photos, maps, diagrams, and videos.
- `claim`: a discrete factual assertion intended for publication.
- `claim_evidence`: evidence supporting or contradicting a claim.
- `research_task`: unresolved questions and verification work.
- `search_document`: generated FTS5 projection.
