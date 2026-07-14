-- Each query should return zero rows.

-- Public questions need evidence.
SELECT vq.archive_code
FROM verified_question vq
LEFT JOIN evidence_link el ON el.verified_question_id=vq.verified_question_id
WHERE vq.public_ready=1
GROUP BY vq.verified_question_id
HAVING COUNT(el.evidence_link_id)=0;

-- Stewart Park agenda items must be linked to Stewart Park.
SELECT ai.archive_code
FROM agenda_item ai
LEFT JOIN project_agenda_item pai ON pai.agenda_item_id=ai.agenda_item_id
WHERE ai.archive_code LIKE 'SP-%'
GROUP BY ai.agenda_item_id
HAVING COUNT(pai.project_id)=0;

-- Stewart Park meetings must be linked to Stewart Park.
SELECT m.archive_code
FROM meeting m
LEFT JOIN project_meeting pm ON pm.meeting_id=m.meeting_id
WHERE m.archive_code LIKE 'SP-%'
GROUP BY m.meeting_id
HAVING COUNT(pm.project_id)=0;

-- Funding events should have evidence when verified.
SELECT fe.archive_code
FROM funding_event fe
WHERE fe.verification_status='verified'
  AND fe.source_document_id IS NULL;
