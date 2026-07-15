from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database" / "archive.db"

checks = []

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")

checks.append(("integrity_check", conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"))
checks.append(("foreign_key_check", len(conn.execute("PRAGMA foreign_key_check").fetchall()) == 0))
checks.append(("tenant_seeded", conn.execute("SELECT COUNT(*) FROM tenant").fetchone()[0] >= 1))
checks.append(("workspace_seeded", conn.execute("SELECT COUNT(*) FROM workspace").fetchone()[0] >= 1))
checks.append(("project_seeded", conn.execute("SELECT COUNT(*) FROM project").fetchone()[0] >= 1))
checks.append(("fts_available", conn.execute("SELECT COUNT(*) FROM search_index").fetchone()[0] >= 0))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}")

conn.close()
if failed:
    raise SystemExit(1)
