-- Stewart Park feature inventory
SELECT archive_code, name, phase_name, feature_status,
       verification_status
FROM project_feature
WHERE project_id = (SELECT project_id FROM project WHERE archive_code='SP')
ORDER BY phase_name, name;
