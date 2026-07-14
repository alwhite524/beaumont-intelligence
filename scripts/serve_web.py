from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
web=Path(__file__).resolve().parents[1]/"website"
os.chdir(web)
print("Open http://127.0.0.1:8000")
ThreadingHTTPServer(("127.0.0.1",8000),SimpleHTTPRequestHandler).serve_forever()
