BEGIN;

INSERT INTO tenant(tenant_id,tenant_code,name,slug)
VALUES('00000000-0000-0000-0000-000000000001','MBF','Move Beaumont Forward','move-beaumont-forward');

INSERT INTO workspace(workspace_id,tenant_id,workspace_code,name,workspace_type)
VALUES('00000000-0000-0000-0000-000000000010',
       '00000000-0000-0000-0000-000000000001',
       'MBF-2026','Move Beaumont Forward 2026','campaign');

INSERT INTO project(project_id,workspace_id,archive_code,name,slug,project_type,summary,status,official_url,start_date)
VALUES('00000000-0000-0000-0000-000000000100',
       '00000000-0000-0000-0000-000000000010',
       'SP','Stewart Park Revitalization','stewart-park','Capital improvement',
       'Source-first project history and intelligence center for the Stewart Park revitalization.',
       'active','https://www.beaumontca.gov/1163/Stewart-Park-Renovation','2022-01-01');

INSERT INTO project_phase(project_phase_id,project_id,archive_code,name,sequence_no,status,description)
VALUES
('00000000-0000-0000-0000-000000000101','00000000-0000-0000-0000-000000000100','SP-PH1','Phase I',1,'active','Currently funded core park improvements.'),
('00000000-0000-0000-0000-000000000102','00000000-0000-0000-0000-000000000100','SP-PH2','Phase II',2,'planned','Additional improvements supported by ORLP grant funding.');

COMMIT;
