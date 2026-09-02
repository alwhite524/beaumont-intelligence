from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
scripts = [
    "build_database.py",
    "import_stewart_park.py",
    "publish_pd_technology.py",
    "refresh_search_index.py",
    "build_research_library_index.py",
    "validate_database.py",
]
for script in scripts:
    print(f"==> {script}")
    subprocess.run([sys.executable, str(ROOT/"scripts"/script)], check=True)
print("Full Stewart Park build complete.")
