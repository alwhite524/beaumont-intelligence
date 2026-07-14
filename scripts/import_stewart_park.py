from pathlib import Path
import csv, json, sqlite3, uuid, sys

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database" / "archive.db"
DATA = ROOT / "data" / "stewart-park"
WORKSPACE_ID = "00000000-0000-0000-0000-000000000010"
PROJECT_ID = "00000000-0000-0000-0000-000000000100"

def uid():
    return str(uuid.uuid4())

def rows(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")

# organizations
org_ids = {}
for r in rows("organizations.csv"):
    oid = uid()
    conn.execute("""INSERT OR REPLACE INTO organization
    (organization_id,workspace_id,archive_code,name,organization_type,official_url)
    VALUES(?,?,?,?,?,?)""",
    (oid,WORKSPACE_ID,r["archive_code"],r["name"],r["organization_type"],r["official_url"] or None))
    org_ids[r["archive_code"]] = oid

# meetings
meeting_ids = {}
for r in rows("meetings.csv"):
    mid = uid()
    conn.execute("""INSERT OR REPLACE INTO meeting
    (meeting_id,workspace_id,archive_code,meeting_date,body_name,meeting_type,
     official_url,minutes_url,video_url,verification_status,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
    (mid,WORKSPACE_ID,r["archive_code"],r["meeting_date"],r["body_name"],r["meeting_type"],
     r["official_url"] or None,r["minutes_url"] or None,r["video_url"] or None,
     r["verification_status"],r["notes"] or None))
    meeting_ids[r["archive_code"]] = mid
    conn.execute("INSERT OR IGNORE INTO project_meeting(project_id,meeting_id,relationship_type) VALUES(?,?,?)",
                 (PROJECT_ID,mid,"substantive"))

# agenda items
agenda_ids = {}
for r in rows("agenda_items.csv"):
    aid = uid()
    conn.execute("""INSERT OR REPLACE INTO agenda_item
    (agenda_item_id,meeting_id,archive_code,item_number,title,category,recommendation,
     action_taken_summary,official_url,verification_status,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
    (aid,meeting_ids[r["meeting_archive_code"]],r["archive_code"],r["item_number"],r["title"],
     r["category"],r["recommendation"] or None,r["action_taken_summary"] or None,
     r["official_url"] or None,r["verification_status"],r["notes"] or None))
    agenda_ids[r["archive_code"]] = aid
    conn.execute("INSERT OR IGNORE INTO project_agenda_item(project_id,agenda_item_id,relationship_type) VALUES(?,?,?)",
                 (PROJECT_ID,aid,"substantive"))

# document types and documents
doc_type_ids={}
doc_ids={}
for r in rows("documents.csv"):
    dtype=r["document_type"]
    if dtype not in doc_type_ids:
        existing=conn.execute("SELECT document_type_id FROM document_type WHERE name=?",(dtype,)).fetchone()
        did=existing[0] if existing else uid()
        if not existing:
            conn.execute("INSERT INTO document_type(document_type_id,name) VALUES(?,?)",(did,dtype))
        doc_type_ids[dtype]=did
    did=uid()
    conn.execute("""INSERT OR REPLACE INTO document
    (document_id,workspace_id,archive_code,title,document_date,document_type_id,official_url,
     publisher,evidence_level,verification_status,summary,accessed_date)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
    (did,WORKSPACE_ID,r["archive_code"],r["title"],r["document_date"] or None,doc_type_ids[dtype],
     r["official_url"],r["publisher"],r["evidence_level"],r["verification_status"],
     r["summary"] or None,r["accessed_date"] or None))
    doc_ids[r["archive_code"]]=did
    conn.execute("INSERT OR IGNORE INTO project_document(project_id,document_id,relationship_type) VALUES(?,?,?)",
                 (PROJECT_ID,did,"related"))

# phases
phase_ids={r[0]:r[1] for r in conn.execute("SELECT archive_code,project_phase_id FROM project_phase WHERE project_id=?",(PROJECT_ID,))}

# features
feature_ids={}
for r in rows("features.csv"):
    fid=uid()
    conn.execute("""INSERT OR REPLACE INTO project_feature
    (project_feature_id,project_id,project_phase_id,archive_code,name,slug,feature_status,
     description,verification_status)
    VALUES(?,?,?,?,?,?,?,?,?)""",
    (fid,PROJECT_ID,phase_ids[r["phase_archive_code"]],r["archive_code"],r["name"],r["slug"],
     r["feature_status"],r["description"],r["verification_status"]))
    feature_ids[r["archive_code"]]=fid
    if "SP-WEB-0001" in doc_ids:
        conn.execute("""INSERT OR IGNORE INTO feature_document
        (project_feature_id,document_id,relationship_type,page_reference)
        VALUES(?,?,?,?)""",(fid,doc_ids["SP-WEB-0001"],"describes","Official project page"))

# funding sources
funding_source_ids={}
for r in rows("funding_sources.csv"):
    fsid=uid()
    conn.execute("""INSERT OR REPLACE INTO funding_source
    (funding_source_id,workspace_id,archive_code,name,source_type,administering_organization_id,description)
    VALUES(?,?,?,?,?,?,?)""",
    (fsid,WORKSPACE_ID,r["archive_code"],r["name"],r["source_type"],
     org_ids.get(r["admin_org_archive_code"]),r["description"] or None))
    funding_source_ids[r["archive_code"]]=fsid

# funding events
for r in rows("funding_events.csv"):
    conn.execute("""INSERT OR REPLACE INTO funding_event
    (funding_event_id,project_id,project_phase_id,funding_source_id,agenda_item_id,archive_code,
     event_date,event_type,amount,amount_status,purpose,verification_status,source_document_id,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (uid(),PROJECT_ID,phase_ids.get(r["phase_archive_code"]),
     funding_source_ids.get(r["funding_source_archive_code"]),
     agenda_ids.get(r["agenda_item_archive_code"]),r["archive_code"],r["event_date"],
     r["event_type"],float(r["amount"]) if r["amount"] else None,r["amount_status"] or None,
     r["purpose"] or None,r["verification_status"],doc_ids.get(r["source_document_archive_code"]),
     r["notes"] or None))

# media
media_ids={}
for r in rows("media.csv"):
    mid=uid()
    conn.execute("""INSERT OR REPLACE INTO media
    (media_id,workspace_id,archive_code,media_type,title,media_date,official_url,local_path,
     source_document_id,verification_status,description)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
    (mid,WORKSPACE_ID,r["archive_code"],r["media_type"],r["title"],r["media_date"] or None,
     r["official_url"] or None,r["local_path"] or None,doc_ids.get(r["source_document_archive_code"]),
     r["verification_status"],r["description"] or None))
    media_ids[r["archive_code"]]=mid
    conn.execute("INSERT OR IGNORE INTO project_media(project_id,media_id,relationship_type) VALUES(?,?,?)",
                 (PROJECT_ID,mid,"current official rendering"))

# questions + evidence
question_ids={}
for r in rows("verified_questions.csv"):
    qid=uid()
    conn.execute("""INSERT OR REPLACE INTO verified_question
    (verified_question_id,project_id,archive_code,category,question,short_answer,detailed_answer,
     status,verification_status,public_ready,created_date,verified_date)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
    (qid,PROJECT_ID,r["archive_code"],r["category"],r["question"],r["short_answer"],
     r["detailed_answer"],r["status"],r["verification_status"],int(r["public_ready"]),
     r["created_date"],r["verified_date"] or None))
    question_ids[r["archive_code"]]=qid

# evidence links
evidence_map = {
    "SP-Q-0001":["SP-NEWS-2025-PAUSE","SP-DOC-2026-0317-UPDATE"],
    "SP-Q-0002":["SP-WEB-0001"],
    "SP-Q-0003":["SP-WEB-0001"],
    "SP-Q-0004":["SP-WEB-0001","SP-NEWS-2026-0601"],
}
for qcode, dcodes in evidence_map.items():
    for i,dcode in enumerate(dcodes,1):
        conn.execute("""INSERT INTO evidence_link
        (evidence_link_id,archive_code,verified_question_id,document_id,support_type)
        VALUES(?,?,?,?,?)""",
        (uid(),f"{qcode}-E{i:02d}",question_ids[qcode],doc_ids[dcode],"supports"))

conn.commit()
print("Imported Stewart Park dataset.")
for table in ["meeting","agenda_item","document","project_feature","funding_event","media","verified_question","evidence_link"]:
    print(table, conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
conn.close()
