from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
scripts = [
    "build_database.py",
    "import_stewart_park.py",
    "refresh_search_index.py",
    "validate_database.py",
]
for script in scripts:
    print(f"==> {script}")
    subprocess.run([sys.executable, str(ROOT/"scripts"/script)], check=True)
print("Full Stewart Park build complete.")
