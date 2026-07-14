from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database" / "archive.db"

conn = sqlite3.connect(DB)
conn.execute("DELETE FROM search_index")

conn.execute("""
INSERT INTO search_index(entity_type,entity_id,archive_code,title,summary,keywords,body_text)
SELECT 'project', project_id, archive_code, name, summary, project_type, ''
FROM project
""")

conn.execute("""
INSERT INTO search_index(entity_type,entity_id,archive_code,title,summary,keywords,body_text)
SELECT 'document', document_id, archive_code, title, summary,
       COALESCE(publisher,'') || ' ' || COALESCE(evidence_level,''),
       ''
FROM document
""")

conn.execute("""
INSERT INTO search_index(entity_type,entity_id,archive_code,title,summary,keywords,body_text)
SELECT 'agenda_item', agenda_item_id, archive_code, title,
       recommendation, category, COALESCE(action_taken_summary,'')
FROM agenda_item
""")

conn.execute("""
INSERT INTO search_index(entity_type,entity_id,archive_code,title,summary,keywords,body_text)
SELECT 'verified_question', verified_question_id, archive_code, question,
       short_answer, category, COALESCE(detailed_answer,'')
FROM verified_question
""")

conn.commit()
print("Search index refreshed.")
conn.close()
