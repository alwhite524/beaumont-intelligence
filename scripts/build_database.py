from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "database" / "archive.db"
SCHEMA = ROOT / "database" / "schema.sql"
SEED_DIR = ROOT / "database" / "seed"
VIEW_DIR = ROOT / "database" / "views"

if DB.exists():
    DB.unlink()

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(SCHEMA.read_text(encoding="utf-8"))

for path in sorted(SEED_DIR.glob("*.sql")):
    conn.executescript(path.read_text(encoding="utf-8"))

for path in sorted(VIEW_DIR.glob("*.sql")):
    conn.executescript(path.read_text(encoding="utf-8"))

conn.commit()
result = conn.execute("PRAGMA integrity_check").fetchone()[0]
conn.close()

if result != "ok":
    print(f"Integrity check failed: {result}", file=sys.stderr)
    raise SystemExit(1)

print(f"Built {DB}")
print("Integrity check: ok")
