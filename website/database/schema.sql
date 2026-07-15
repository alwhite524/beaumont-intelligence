PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================================
-- TENANCY / DEPLOYMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS tenant (
    tenant_id TEXT PRIMARY KEY,
    tenant_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workspace (
    workspace_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenant(tenant_id),
    workspace_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    workspace_type TEXT NOT NULL DEFAULT 'campaign',
    status TEXT NOT NULL DEFAULT 'active',
    created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CORE PROJECT MODEL
-- ============================================================

CREATE TABLE IF NOT EXISTS project (
    project_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    project_type TEXT,
    summary TEXT,
    status TEXT,
    official_url TEXT,
    start_date TEXT,
    target_completion_date TEXT,
    actual_completion_date TEXT,
    latitude REAL,
    longitude REAL,
    created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, slug)
);

CREATE TABLE IF NOT EXISTS project_phase (
    project_phase_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    sequence_no INTEGER NOT NULL DEFAULT 1,
    status TEXT,
    start_date TEXT,
    end_date TEXT,
    description TEXT,
    UNIQUE(project_id, name)
);

CREATE TABLE IF NOT EXISTS project_feature (
    project_feature_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    project_phase_id TEXT REFERENCES project_phase(project_phase_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    feature_status TEXT,
    description TEXT,
    first_mention_date TEXT,
    first_rendering_date TEXT,
    approval_date TEXT,
    completion_date TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    UNIQUE(project_id, slug)
);

-- ============================================================
-- MEETINGS / ACTIONS / VIDEO
-- ============================================================

CREATE TABLE IF NOT EXISTS meeting (
    meeting_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    meeting_date TEXT NOT NULL,
    body_name TEXT NOT NULL,
    meeting_type TEXT,
    start_time_local TEXT,
    timezone TEXT DEFAULT 'America/Los_Angeles',
    official_url TEXT,
    minutes_url TEXT,
    video_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    notes TEXT,
    UNIQUE(workspace_id, body_name, meeting_date, meeting_type)
);

CREATE TABLE IF NOT EXISTS agenda_item (
    agenda_item_id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meeting(meeting_id),
    archive_code TEXT NOT NULL UNIQUE,
    item_number TEXT,
    title TEXT NOT NULL,
    category TEXT,
    recommendation TEXT,
    action_taken_summary TEXT,
    official_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    notes TEXT,
    UNIQUE(meeting_id, item_number, title)
);

CREATE TABLE IF NOT EXISTS council_action (
    council_action_id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_item(agenda_item_id),
    archive_code TEXT NOT NULL UNIQUE,
    action_sequence INTEGER NOT NULL DEFAULT 1,
    action_type TEXT,
    motion_text TEXT,
    mover_name TEXT,
    seconder_name TEXT,
    result TEXT,
    vote_text TEXT,
    yes_count INTEGER,
    no_count INTEGER,
    abstain_count INTEGER,
    absent_count INTEGER,
    recusal_text TEXT,
    effective_date TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT,
    source_page_reference TEXT,
    notes TEXT,
    UNIQUE(agenda_item_id, action_sequence)
);

CREATE TABLE IF NOT EXISTS video_segment (
    video_segment_id TEXT PRIMARY KEY,
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    council_action_id TEXT REFERENCES council_action(council_action_id),
    archive_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    start_seconds INTEGER NOT NULL CHECK(start_seconds >= 0),
    end_seconds INTEGER CHECK(end_seconds IS NULL OR end_seconds >= start_seconds),
    speaker_name TEXT,
    topic TEXT,
    transcript TEXT,
    direct_url TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed'
);

CREATE TABLE IF NOT EXISTS project_meeting (
    project_id TEXT NOT NULL REFERENCES project(project_id),
    meeting_id TEXT NOT NULL REFERENCES meeting(meeting_id),
    relationship_type TEXT NOT NULL DEFAULT 'substantive',
    PRIMARY KEY(project_id, meeting_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS project_agenda_item (
    project_id TEXT NOT NULL REFERENCES project(project_id),
    agenda_item_id TEXT NOT NULL REFERENCES agenda_item(agenda_item_id),
    relationship_type TEXT NOT NULL DEFAULT 'substantive',
    PRIMARY KEY(project_id, agenda_item_id, relationship_type)
);

-- ============================================================
-- DOCUMENTS / EVIDENCE / MEDIA
-- ============================================================

CREATE TABLE IF NOT EXISTS document_type (
    document_type_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS document (
    document_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    document_date TEXT,
    document_type_id TEXT REFERENCES document_type(document_type_id),
    official_url TEXT NOT NULL,
    publisher TEXT,
    evidence_level TEXT NOT NULL CHECK(evidence_level IN ('A','B','C','D')),
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    summary TEXT,
    extracted_text_path TEXT,
    content_hash TEXT,
    accessed_date TEXT,
    supersedes_document_id TEXT REFERENCES document(document_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS project_document (
    project_id TEXT NOT NULL REFERENCES project(project_id),
    document_id TEXT NOT NULL REFERENCES document(document_id),
    relationship_type TEXT NOT NULL DEFAULT 'related',
    PRIMARY KEY(project_id, document_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS agenda_item_document (
    agenda_item_id TEXT NOT NULL REFERENCES agenda_item(agenda_item_id),
    document_id TEXT NOT NULL REFERENCES document(document_id),
    relationship_type TEXT NOT NULL DEFAULT 'attachment',
    PRIMARY KEY(agenda_item_id, document_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL,
    title TEXT NOT NULL,
    media_date TEXT,
    official_url TEXT,
    local_path TEXT,
    source_document_id TEXT REFERENCES document(document_id),
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    description TEXT,
    width_px INTEGER,
    height_px INTEGER,
    content_hash TEXT
);

CREATE TABLE IF NOT EXISTS project_media (
    project_id TEXT NOT NULL REFERENCES project(project_id),
    media_id TEXT NOT NULL REFERENCES media(media_id),
    relationship_type TEXT NOT NULL DEFAULT 'related',
    PRIMARY KEY(project_id, media_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS feature_document (
    project_feature_id TEXT NOT NULL REFERENCES project_feature(project_feature_id),
    document_id TEXT NOT NULL REFERENCES document(document_id),
    relationship_type TEXT NOT NULL DEFAULT 'mentions',
    page_reference TEXT NOT NULL DEFAULT '',
    PRIMARY KEY(project_feature_id, document_id, relationship_type, page_reference)
);

CREATE TABLE IF NOT EXISTS feature_media (
    project_feature_id TEXT NOT NULL REFERENCES project_feature(project_feature_id),
    media_id TEXT NOT NULL REFERENCES media(media_id),
    relationship_type TEXT NOT NULL DEFAULT 'depicts',
    PRIMARY KEY(project_feature_id, media_id, relationship_type)
);

-- ============================================================
-- ORGANIZATIONS / PEOPLE / ROLES
-- ============================================================

CREATE TABLE IF NOT EXISTS organization (
    organization_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    organization_type TEXT,
    official_url TEXT,
    UNIQUE(workspace_id, name)
);

CREATE TABLE IF NOT EXISTS person (
    person_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    title TEXT,
    organization_id TEXT REFERENCES organization(organization_id),
    notes TEXT,
    UNIQUE(workspace_id, display_name, title)
);

CREATE TABLE IF NOT EXISTS project_organization (
    project_id TEXT NOT NULL REFERENCES project(project_id),
    organization_id TEXT NOT NULL REFERENCES organization(organization_id),
    role_name TEXT NOT NULL,
    start_date TEXT NOT NULL DEFAULT '',
    end_date TEXT,
    PRIMARY KEY(project_id, organization_id, role_name, start_date)
);

-- ============================================================
-- FUNDING / CONTRACTS
-- ============================================================

CREATE TABLE IF NOT EXISTS funding_source (
    funding_source_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_type TEXT,
    administering_organization_id TEXT REFERENCES organization(organization_id),
    description TEXT,
    UNIQUE(workspace_id, name)
);

CREATE TABLE IF NOT EXISTS funding_event (
    funding_event_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    project_phase_id TEXT REFERENCES project_phase(project_phase_id),
    funding_source_id TEXT REFERENCES funding_source(funding_source_id),
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    archive_code TEXT NOT NULL UNIQUE,
    event_date TEXT,
    event_type TEXT NOT NULL,
    amount REAL,
    amount_status TEXT,
    purpose TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT REFERENCES document(document_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS contract (
    contract_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    organization_id TEXT NOT NULL REFERENCES organization(organization_id),
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    archive_code TEXT NOT NULL UNIQUE,
    contract_type TEXT,
    title TEXT NOT NULL,
    original_amount REAL,
    current_amount REAL,
    award_date TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT REFERENCES document(document_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS contract_amendment (
    contract_amendment_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL REFERENCES contract(contract_id),
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    archive_code TEXT NOT NULL UNIQUE,
    amendment_no INTEGER,
    amendment_date TEXT,
    amount_change REAL,
    revised_contract_amount REAL,
    purpose TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    source_document_id TEXT REFERENCES document(document_id),
    notes TEXT
);

-- ============================================================
-- QUESTIONS / CLAIMS / EVIDENCE
-- ============================================================

CREATE TABLE IF NOT EXISTS verified_question (
    verified_question_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES project(project_id),
    archive_code TEXT NOT NULL UNIQUE,
    category TEXT,
    question TEXT NOT NULL,
    short_answer TEXT,
    detailed_answer TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    public_ready INTEGER NOT NULL DEFAULT 0 CHECK(public_ready IN (0,1)),
    created_date TEXT NOT NULL,
    verified_date TEXT,
    UNIQUE(project_id, question)
);

CREATE TABLE IF NOT EXISTS claim (
    claim_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES project(project_id),
    verified_question_id TEXT REFERENCES verified_question(verified_question_id),
    archive_code TEXT NOT NULL UNIQUE,
    claim_text TEXT NOT NULL,
    claim_date TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unreviewed',
    public_ready INTEGER NOT NULL DEFAULT 0 CHECK(public_ready IN (0,1)),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence_link (
    evidence_link_id TEXT PRIMARY KEY,
    archive_code TEXT NOT NULL UNIQUE,
    claim_id TEXT REFERENCES claim(claim_id),
    verified_question_id TEXT REFERENCES verified_question(verified_question_id),
    document_id TEXT REFERENCES document(document_id),
    agenda_item_id TEXT REFERENCES agenda_item(agenda_item_id),
    council_action_id TEXT REFERENCES council_action(council_action_id),
    video_segment_id TEXT REFERENCES video_segment(video_segment_id),
    media_id TEXT REFERENCES media(media_id),
    support_type TEXT NOT NULL DEFAULT 'supports',
    page_reference TEXT,
    note TEXT,
    CHECK (
        claim_id IS NOT NULL OR
        verified_question_id IS NOT NULL
    ),
    CHECK (
        document_id IS NOT NULL OR
        agenda_item_id IS NOT NULL OR
        council_action_id IS NOT NULL OR
        video_segment_id IS NOT NULL OR
        media_id IS NOT NULL
    )
);

-- ============================================================
-- TAGS / SEARCH / OPERATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS topic (
    topic_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    archive_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    UNIQUE(workspace_id, slug)
);

CREATE TABLE IF NOT EXISTS entity_topic (
    entity_topic_id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topic(topic_id),
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    relevance INTEGER NOT NULL DEFAULT 3 CHECK(relevance BETWEEN 1 AND 5),
    UNIQUE(topic_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS research_task (
    research_task_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspace(workspace_id),
    project_id TEXT REFERENCES project(project_id),
    archive_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'open',
    assigned_to TEXT,
    due_date TEXT,
    resolution_notes TEXT
);

CREATE TABLE IF NOT EXISTS source_audit (
    source_audit_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES document(document_id),
    checked_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    http_status INTEGER,
    final_url TEXT,
    content_hash TEXT,
    is_broken INTEGER NOT NULL DEFAULT 0 CHECK(is_broken IN (0,1)),
    notes TEXT
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_project_workspace ON project(workspace_id, status);
CREATE INDEX IF NOT EXISTS ix_meeting_date ON meeting(meeting_date);
CREATE INDEX IF NOT EXISTS ix_agenda_meeting ON agenda_item(meeting_id, item_number);
CREATE INDEX IF NOT EXISTS ix_action_agenda ON council_action(agenda_item_id, verification_status);
CREATE INDEX IF NOT EXISTS ix_video_agenda ON video_segment(agenda_item_id, start_seconds);
CREATE INDEX IF NOT EXISTS ix_document_date ON document(document_date);
CREATE INDEX IF NOT EXISTS ix_document_verify ON document(verification_status, evidence_level);
CREATE INDEX IF NOT EXISTS ix_funding_project ON funding_event(project_id, event_date);
CREATE INDEX IF NOT EXISTS ix_contract_project ON contract(project_id, award_date);
CREATE INDEX IF NOT EXISTS ix_question_project ON verified_question(project_id, status);
CREATE INDEX IF NOT EXISTS ix_claim_project ON claim(project_id, public_ready);
CREATE INDEX IF NOT EXISTS ix_research_status ON research_task(status, priority);

-- ============================================================
-- FULL TEXT SEARCH
-- ============================================================

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    entity_type UNINDEXED,
    entity_id UNINDEXED,
    archive_code UNINDEXED,
    title,
    summary,
    keywords,
    body_text,
    tokenize='porter unicode61'
);
