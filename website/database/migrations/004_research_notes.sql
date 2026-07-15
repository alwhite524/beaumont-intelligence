CREATE TABLE IF NOT EXISTS research_note (
    research_note_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    project_id TEXT REFERENCES project(project_id),
    question TEXT NOT NULL,
    answer TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    public_ready INTEGER NOT NULL DEFAULT 0 CHECK(public_ready IN (0,1)),
    created_date TEXT NOT NULL,
    verified_date TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS research_note_evidence (
    research_note_id TEXT NOT NULL REFERENCES research_note(research_note_id),
    document_id TEXT NOT NULL REFERENCES document(document_id),
    support_type TEXT NOT NULL DEFAULT 'supports',
    page_reference TEXT NOT NULL DEFAULT '',
    PRIMARY KEY(research_note_id, document_id, support_type, page_reference)
);

CREATE INDEX IF NOT EXISTS ix_research_note_status
ON research_note(status, verification_status);
