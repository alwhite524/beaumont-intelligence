-- Project dashboard
SELECT * FROM vw_project_dashboard ORDER BY name;

-- Stewart Park Council action register
SELECT *
FROM vw_council_action_register
WHERE project_code = 'SP'
ORDER BY meeting_date, item_number, action_code;

-- Open verification work
SELECT *
FROM vw_verification_queue
ORDER BY entity_type, archive_code;

-- Evidence for a question or claim
SELECT *
FROM vw_evidence_explorer
WHERE knowledge_code = :knowledge_code;

-- Full-text search
SELECT entity_type, archive_code, title,
       snippet(search_index, 4, '[', ']', ' … ', 12) AS match
FROM search_index
WHERE search_index MATCH :query
ORDER BY rank;
