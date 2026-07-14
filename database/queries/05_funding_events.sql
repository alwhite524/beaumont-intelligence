-- Funding and grant events
SELECT fe.event_date, fs.name AS funding_source, fe.event_type,
       fe.amount, fe.amount_status, fe.phase_name, fe.verification_status
FROM funding_event fe
LEFT JOIN funding_source fs ON fs.funding_source_id = fe.funding_source_id
WHERE fe.project_id = (SELECT project_id FROM project WHERE archive_code='SP')
ORDER BY fe.event_date;
