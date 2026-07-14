CREATE TABLE IF NOT EXISTS council_action (
    council_action_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_item(agenda_item_id),
    action_sequence INTEGER NOT NULL DEFAULT 1,
    motion_text TEXT,
    action_type TEXT,
    result TEXT,
    vote_text TEXT,
    effective_date TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT REFERENCES document(document_id),
    source_page_reference TEXT,
    notes TEXT,
    UNIQUE(agenda_item_id, action_sequence)
);

CREATE TABLE IF NOT EXISTS funding_source (
    funding_source_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    source_type TEXT,
    administering_organization_id TEXT REFERENCES organization(organization_id),
    description TEXT
);

CREATE TABLE IF NOT EXISTS funding_event (
    funding_event_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    funding_source_id TEXT REFERENCES funding_source(funding_source_id),
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    event_date TEXT,
    event_type TEXT NOT NULL,
    amount REAL,
    amount_status TEXT,
    purpose TEXT,
    phase_name TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT REFERENCES document(document_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS project_feature (
    project_feature_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    phase_name TEXT,
    feature_status TEXT,
    description TEXT,
    first_mention_date TEXT,
    first_rendering_date TEXT,
    approval_date TEXT,
    completion_date TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    UNIQUE(project_id, slug)
);

CREATE TABLE IF NOT EXISTS document_feature (
    document_id TEXT NOT NULL REFERENCES document(document_id),
    project_feature_id TEXT NOT NULL REFERENCES project_feature(project_feature_id),
    relationship_type TEXT NOT NULL DEFAULT 'mentions',
    page_reference TEXT,
    PRIMARY KEY(document_id, project_feature_id, relationship_type, page_reference)
);

CREATE TABLE IF NOT EXISTS agenda_item_feature (
    agenda_item_id TEXT NOT NULL REFERENCES agenda_item(agenda_item_id),
    project_feature_id TEXT NOT NULL REFERENCES project_feature(project_feature_id),
    relationship_type TEXT NOT NULL DEFAULT 'mentions',
    PRIMARY KEY(agenda_item_id, project_feature_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS media_feature (
    media_id TEXT NOT NULL REFERENCES media(media_id),
    project_feature_id TEXT NOT NULL REFERENCES project_feature(project_feature_id),
    relationship_type TEXT NOT NULL DEFAULT 'depicts',
    PRIMARY KEY(media_id, project_feature_id, relationship_type)
);

CREATE VIEW IF NOT EXISTS vw_agenda_action_status AS
SELECT
    ai.archive_code AS agenda_item_code,
    m.meeting_date,
    ai.item_number,
    ai.title,
    ai.timestamp_status,
    COUNT(ca.council_action_id) AS action_count,
    SUM(CASE WHEN ca.verification_status = 'verified' THEN 1 ELSE 0 END) AS verified_action_count
FROM agenda_item ai
JOIN meeting m ON m.meeting_id = ai.meeting_id
LEFT JOIN council_action ca ON ca.agenda_item_id = ai.agenda_item_id
GROUP BY ai.agenda_item_id;

CREATE VIEW IF NOT EXISTS vw_project_feature_timeline AS
SELECT
    p.archive_code AS project_code,
    pf.archive_code AS feature_code,
    pf.name,
    pf.phase_name,
    pf.feature_status,
    pf.first_mention_date,
    pf.first_rendering_date,
    pf.approval_date,
    pf.completion_date,
    pf.verification_status
FROM project_feature pf
JOIN project p ON p.project_id = pf.project_id;
