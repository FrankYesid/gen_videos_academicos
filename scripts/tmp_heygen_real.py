import json
import sys
import time
import urllib.request
import urllib.error

COURSE_ID = "c9a38b4a-c479-4358-a757-3d58d4c0f613"
URL = f"http://localhost:8000/api/v1/courses/{COURSE_ID}/generate-video"

print(f"POST {URL} body=undefined => default provider=HEYGEN_MODE=heygen_agent", flush=True)
print("=" * 72, flush=True)
req = urllib.request.Request(URL, method="POST", headers={"Content-Type": "application/json"})
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=360) as resp:
        raw = resp.read().decode("utf-8")
        dt = time.time() - t0
        print(f"STATUS {resp.status} OK (⏱ {dt:.1f}s)", flush=True)
        obj = json.loads(raw)
        print(json.dumps(obj, indent=2, ensure_ascii=False)[:5000], flush=True)
except urllib.error.HTTPError as e:
    dt = time.time() - t0
    raw = e.read().decode("utf-8")
    print(f"STATUS HTTP {e.code} ⏱ {dt:.1f}s", flush=True)
    try:
        obj = json.loads(raw)
        print(json.dumps(obj, indent=2, ensure_ascii=False)[:5000], flush=True)
    except Exception:
        print(raw[:5000], flush=True)
    sys.exit(1)
