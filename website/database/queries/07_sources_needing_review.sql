-- Sources not yet fully verified
SELECT archive_code, title, document_date, evidence_level,
       verification_status, official_url
FROM document
WHERE verification_status <> 'verified'
ORDER BY document_date;
