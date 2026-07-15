-- All Stewart Park meetings
SELECT m.meeting_date, ai.item_number, ai.title, ai.official_url,
       ai.timestamp_status
FROM meeting m
JOIN project_meeting pm ON pm.meeting_id = m.meeting_id
JOIN project p ON p.project_id = pm.project_id
LEFT JOIN agenda_item ai ON ai.meeting_id = m.meeting_id
WHERE p.archive_code = 'SP'
ORDER BY m.meeting_date, ai.item_number;
