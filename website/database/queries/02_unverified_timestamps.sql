-- Agenda items that still need video timestamp verification
SELECT m.meeting_date, ai.item_number, ai.title, ai.official_url
FROM agenda_item ai
JOIN meeting m ON m.meeting_id = ai.meeting_id
WHERE ai.timestamp_status <> 'verified'
ORDER BY m.meeting_date;
