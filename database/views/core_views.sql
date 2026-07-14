CREATE VIEW IF NOT EXISTS vw_project_dashboard AS
SELECT
    p.project_id,
    p.archive_code,
    p.name,
    p.status,
    COUNT(DISTINCT pm.meeting_id) AS meeting_count,
    COUNT(DISTINCT pai.agenda_item_id) AS agenda_item_count,
    COUNT(DISTINCT pd.document_id) AS document_count,
    COUNT(DISTINCT pmed.media_id) AS media_count,
    COUNT(DISTINCT pf.project_feature_id) AS feature_count,
    COUNT(DISTINCT fe.funding_event_id) AS funding_event_count,
    COUNT(DISTINCT c.contract_id) AS contract_count,
    COUNT(DISTINCT vq.verified_question_id) AS verified_question_count
FROM project p
LEFT JOIN project_meeting pm ON pm.project_id = p.project_id
LEFT JOIN project_agenda_item pai ON pai.project_id = p.project_id
LEFT JOIN project_document pd ON pd.project_id = p.project_id
LEFT JOIN project_media pmed ON pmed.project_id = p.project_id
LEFT JOIN project_feature pf ON pf.project_id = p.project_id
LEFT JOIN funding_event fe ON fe.project_id = p.project_id
LEFT JOIN contract c ON c.project_id = p.project_id
LEFT JOIN verified_question vq ON vq.project_id = p.project_id
GROUP BY p.project_id;

CREATE VIEW IF NOT EXISTS vw_council_action_register AS
SELECT
    p.archive_code AS project_code,
    m.meeting_date,
    ai.item_number,
    ai.title AS agenda_title,
    ca.archive_code AS action_code,
    ca.action_type,
    ca.motion_text,
    ca.mover_name,
    ca.seconder_name,
    ca.result,
    ca.vote_text,
    ca.verification_status,
    m.minutes_url,
    m.video_url
FROM council_action ca
JOIN agenda_item ai ON ai.agenda_item_id = ca.agenda_item_id
JOIN meeting m ON m.meeting_id = ai.meeting_id
JOIN project_agenda_item pai ON pai.agenda_item_id = ai.agenda_item_id
JOIN project p ON p.project_id = pai.project_id;

CREATE VIEW IF NOT EXISTS vw_evidence_explorer AS
SELECT
    el.archive_code AS evidence_code,
    COALESCE(c.archive_code, vq.archive_code) AS knowledge_code,
    COALESCE(c.claim_text, vq.question) AS knowledge_text,
    el.support_type,
    d.archive_code AS document_code,
    d.title AS document_title,
    d.official_url AS document_url,
    ai.archive_code AS agenda_code,
    ai.title AS agenda_title,
    ca.archive_code AS action_code,
    vs.archive_code AS video_segment_code,
    vs.direct_url AS video_url,
    med.archive_code AS media_code,
    med.official_url AS media_url,
    el.page_reference,
    el.note
FROM evidence_link el
LEFT JOIN claim c ON c.claim_id = el.claim_id
LEFT JOIN verified_question vq ON vq.verified_question_id = el.verified_question_id
LEFT JOIN document d ON d.document_id = el.document_id
LEFT JOIN agenda_item ai ON ai.agenda_item_id = el.agenda_item_id
LEFT JOIN council_action ca ON ca.council_action_id = el.council_action_id
LEFT JOIN video_segment vs ON vs.video_segment_id = el.video_segment_id
LEFT JOIN media med ON med.media_id = el.media_id;

CREATE VIEW IF NOT EXISTS vw_verification_queue AS
SELECT 'document' AS entity_type, document_id AS entity_id, archive_code, title,
       verification_status
FROM document
WHERE verification_status <> 'verified'
UNION ALL
SELECT 'agenda_item', agenda_item_id, archive_code, title, verification_status
FROM agenda_item
WHERE verification_status <> 'verified'
UNION ALL
SELECT 'council_action', council_action_id, archive_code,
       COALESCE(motion_text, action_type, 'Council action'), verification_status
FROM council_action
WHERE verification_status <> 'verified'
UNION ALL
SELECT 'video_segment', video_segment_id, archive_code, title, verification_status
FROM video_segment
WHERE verification_status <> 'verified'
UNION ALL
SELECT 'verified_question', verified_question_id, archive_code, question,
       verification_status
FROM verified_question
WHERE verification_status <> 'verified';
