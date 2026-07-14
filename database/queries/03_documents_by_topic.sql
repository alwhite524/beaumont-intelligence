-- Search source metadata by topic/keyword
SELECT archive_code, title, document_date, official_url, verification_status
FROM document
WHERE title LIKE '%' || :keyword || '%'
   OR summary LIKE '%' || :keyword || '%'
ORDER BY document_date;
