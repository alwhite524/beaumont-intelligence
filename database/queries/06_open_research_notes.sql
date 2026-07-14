-- Open research questions
SELECT archive_code, question, status, verification_status
FROM research_note
WHERE status <> 'answered' OR verification_status <> 'verified'
ORDER BY archive_code;
