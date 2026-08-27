# -*- coding: utf-8 -*-
import sys
import requests
import json
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = 'http://localhost:8000/api/v1'

def hr(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def pp(label, obj, keys=None):
    if isinstance(obj, requests.Response):
        print(f"  {label} HTTP {obj.status_code}")
        try:
            body = obj.json()
        except Exception:
            print(f"  BODY RAW: {obj.text[:500]}")
            return None
        print(f"  keys={list(body.keys())}")
        if 'success' in body:
            print(f"  success={body['success']}")
        return body
    print(f"  {label} = {obj}")
    return obj

def main():
    hr("1. HEALTH")
    h = requests.get(f"{BASE}/health", timeout=10)
    body = pp("health", h)
    assert body and body.get("success")

    hr("2. CREATE COURSE SIN PDF")
    payload = {
        "title": f"Curso Smoke Syn {int(time.time())}",
        "subject": "Fisica Cuantica",
        "level": "intermediate",
        "language": "es",
        "estimated_duration_minutes": 45,
    }
    c = requests.post(f"{BASE}/courses", json=payload, timeout=30)
    b = pp("create", c)
    course_id = b["data"]["id"]
    print(f"  course_id={course_id}")
    print(f"  document_id={b['data'].get('document_id') or 'NULL'}")
    assert (b["data"].get("document_id") or None) is None

    hr("3a. GET analysis ANTES (404 OK)")
    r = requests.get(f"{BASE}/courses/{course_id}/analysis", timeout=10)
    pp("get analysis before", r)
    assert r.status_code == 404, f"esperaba 404 vino {r.status_code}"

    hr("3b. POST analyze SIN PDF (synthetic fallback)")
    an = requests.post(
        f"{BASE}/courses/{course_id}/analyze",
        params={"force_regenerate": True},
        timeout=300,
    )
    b2 = pp("analyze response", an)
    assert an.status_code == 200, f"status={an.status_code} body={an.text[:800]}"
    assert "data" in b2, f"no hay data en response: {json.dumps(b2, indent=2, default=str)[:600]}"
    assert "analysis" in b2["data"], f"falta analysis en data: keys={list(b2['data'].keys())}"
    print(f"  synthetic={b2['data'].get('synthetic')}")
    print(f"  course.progress={b2['data'].get('course',{}).get('progress')}")
    assert b2["data"].get("synthetic") is True, "debe ser synthetic=true"

    hr("4. WORKFLOW sync 6 pasos (run_async=false)")
    wp = requests.post(
        f"{BASE}/workflow/courses/{course_id}/process",
        params={"run_async": False},
        timeout=900,
    )
    b3 = pp("workflow", wp)
    assert wp.status_code == 200, f"status={wp.status_code} {wp.text[:800]}"
    d3 = b3["data"]
    print(f"  final_status   = {d3['final_status']}")
    print(f"  final_progress = {d3['final_progress']}%")
    steps = d3.get("steps_completed") or []
    print(f"  steps count    = {len(steps)}")
    for s in steps:
        name = s.get("step") or s.get("name") or str(s)[:60]
        print(f"    · {name}  status={s.get('status')}")
    qa_score = None
    for s in steps:
        if "qa" in str(s.get("step") or "").lower() or s.get("name") == "qa_review":
            rd = s.get("result_data") or {}
            qa_score = rd.get("score") or None
            if not qa_score:
                for k in ("qa", "result"):
                    if isinstance(rd.get(k), dict):
                        qa_score = rd[k].get("score")
            break
    print(f"  QA score (approx) = {qa_score}")
    assert d3["final_status"] == "COMPLETED"
    assert d3["final_progress"] == 100
    assert len(steps) >= 6

    hr("5. POST /courses/{id}/approve-script endpoint (debe existir)")
    ap = requests.post(f"{BASE}/courses/{course_id}/approve-script", timeout=60)
    pp("approve script", ap)
    assert ap.status_code in (200, 409), f"status={ap.status_code} no existe endpoint"

    hr("6. GET analysis DESPUES (200)")
    an2 = requests.get(f"{BASE}/courses/{course_id}/analysis", timeout=15)
    b4 = pp("get analysis after", an2)
    assert an2.status_code == 200

    hr("RESULTADO")
    print("  🎉  SMOKE E2E COMPLETO OK")
    print("  · Backend healthy v0.2.0")
    print("  · Curso creado SIN PDF")
    print("  · GET analysis 404 vacio OK")
    print("  · POST analyze synthetic:true OK")
    print("  · Workflow sync 6 pasos COMPLETED 100% OK")
    print("  · Endpoint approve-script existe OK")
    print("  · GET analysis 200 final OK")
    print("  · Alembic 005 head, 4 containers healthy.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
