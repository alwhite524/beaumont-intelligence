-- Data-quality assertions. Each query should return zero rows.

-- Public-ready questions must be verified.
SELECT archive_code
FROM verified_question
WHERE public_ready = 1 AND verification_status <> 'verified';

-- Public-ready claims must be verified.
SELECT archive_code
FROM claim
WHERE public_ready = 1 AND verification_status <> 'verified';

-- Evidence links must point to a knowledge object and at least one source.
SELECT archive_code
FROM evidence_link
WHERE (claim_id IS NULL AND verified_question_id IS NULL)
   OR (document_id IS NULL AND agenda_item_id IS NULL AND council_action_id IS NULL
       AND video_segment_id IS NULL AND media_id IS NULL);

-- Verified actions should have an outcome.
SELECT archive_code
FROM council_action
WHERE verification_status = 'verified'
  AND COALESCE(result,'') = '';

-- Verified video segments should have a direct URL.
SELECT archive_code
FROM video_segment
WHERE verification_status = 'verified'
  AND COALESCE(direct_url,'') = '';
