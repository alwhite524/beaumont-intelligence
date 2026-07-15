-- v0.2 meeting inventory support
ALTER TABLE agenda_item ADD COLUMN category TEXT;
ALTER TABLE agenda_item ADD COLUMN source_type TEXT;
ALTER TABLE agenda_item ADD COLUMN evidence_level TEXT;
