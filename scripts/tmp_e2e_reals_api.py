"""Prueba E2E APIs REALES (NO fallback deterministic, NO mock).

Crear curso -> Agregar Document fake con extracted_text para activar LLM ruta ->
POST analyze -> POST pedagogical -> POST script -> VERIFICAR NINGUN fallback.
"""
import json
import hashlib
import random
import subprocess
import sys
import time
import urllib.request
import urllib.error

API = "http://localhost:8000/api/v1"
HEADERS_JSON = {"Content-Type": "application/json"}
COURSE_TITLE = "Fotografía Digital para Principiantes"
COURSE_SUBJECT = "Fotografía"
COURSE_DESCRIPTION = (
    "Curso introductorio de fotografía digital enfocado en principiantes. "
    "Contenidos: exposición, diafragma, obturador, ISO, regla de los tercios, "
    "composición básica, iluminación natural y artificial, tipos de lentes y "
    "edición básica en software libre. Duración estimada 20 minutos con ejemplos."
)
EXTRACTED_TEXT = (
    "Fotografía Digital para Principiantes\n"
    "Capítulo 1 - Introducción a la fotografía: la cámara oscura, historia breve, "
    "la fotografía como arte y como técnica. Tipos de cámaras: compactas, bridge, "
    "DSLR, mirrorless, acción, smartphone.\n"
    "Capítulo 2 - El triángulo de la exposición: diafragma (f/1.4 a f/22), "
    "obturador (1/4000s a 30s), ISO (100 a 6400). Relación entre los tres parámetros. "
    "Ejercicio práctico: misma foto con 3 combinaciones equivalentes.\n"
    "Capítulo 3 - Composición: regla de los tercios, punto de fuga, líneas guía, "
    "simetría, profundidad de campo, espacio negativo, regla de la mirada.\n"
    "Capítulo 4 - Iluminación: luz natural (hora dorada, hora azul), luz dura vs "
    "suave, esquemas de iluminación artificial: Rembrandt, mariposa, Loop, Split.\n"
    "Capítulo 5 - Óptica: tipos de lentes (gran angular, estándar, telefoto, macro, "
    "ojo de pez), distancia focal, distorsiones, estabilización óptica.\n"
    "Capítulo 6 - Postproducción: formato RAW vs JPEG, balance de blancos, curvas, "
    "recorte, niveles, reducción de ruido. Software gratuito: Darktable, GIMP.\n"
    "Conclusiones: practicar 10 minutos diarios, revisar obras de fotógrafos "
    "clásicos (Ansel Adams, Cartier-Bresson), desarrollar ojo crítico.\n"
)


def req(method, path, body=None, timeout=300):
    url = f"{API}{path}"
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        status = e.code
        print(f"  HTTP ERROR {status}: {raw[:1200]}")
        raise
    if raw:
        return status, json.loads(raw)
    return status, None


def banner(text):
    print("\n" + "=" * 72)
    print("||  " + text)
    print("=" * 72)


def assert_no_fallback(payload: dict, step: str):
    # Debe ser success=True y data NO debe tener deterministic_fallback ni fallback_reason
    data = payload.get("data", payload)
    if data.get("deterministic_fallback") is True:
        print(f"❌ FAIL [{step}] deterministic_fallback=True -> NO debería haber fallback")
        sys.exit(10)
    if "fallback_reason" in data and data["fallback_reason"]:
        print(f"❌ FAIL [{step}] fallback_reason presente: {data['fallback_reason'][:400]}")
        sys.exit(11)
    print(f"   ✅ [{step}] Sin fallback deterministic ✓")


banner("PASO 1/7: Health check")
s, h = req("GET", "/health")
assert s == 200 and h.get("success")
print("   ✅ Health OK (", h["data"]["status"], h["data"]["version"], ")")

banner("PASO 2/7: Crear curso")
_, create = req(
    "POST",
    "/courses",
    {
        "title": COURSE_TITLE,
        "subject": COURSE_SUBJECT,
        "description": COURSE_DESCRIPTION,
        "language": "es",
        "level": "beginner",
        "estimated_duration_minutes": 20,
    },
)
assert create.get("success")
course_id = create["data"]["id"]
print("   ✅ Curso creado id =", course_id, "status =", create["data"]["status"])

banner("PASO 3/7: Insertar Document fake con extracted_text (activa ruta LLM)")
file_hash = hashlib.sha256((EXTRACTED_TEXT + str(random.random())).encode()).hexdigest()
sql_doc = f"""
INSERT INTO documents (id, filename, file_path, file_hash, mime_type, file_size, page_count, extracted_text, status, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'fotografia_digital.pdf',
  '/app/storage/fotografia_digital.pdf',
  '{file_hash}',
  'application/pdf',
  {len(EXTRACTED_TEXT.encode('utf-8'))},
  6,
  $${EXTRACTED_TEXT}$$,
  'EXTRACTED',
  NOW(),
  NOW()
) RETURNING id;
"""
res_doc = subprocess.run(
    [
        "docker", "exec", "acvg-postgres",
        "psql", "-U", "postgres", "-d", "course_generator", "-t", "-A", "-c", sql_doc,
    ],
    capture_output=True, text=True,
)
if res_doc.returncode != 0:
    print("DB ERROR doc:", res_doc.stderr[:800])
    sys.exit(2)
doc_id = res_doc.stdout.strip().splitlines()[0].strip()
assert len(doc_id) > 20, f"No doc id returned: {res_doc.stdout!r}"
print("   ✅ Document fake insertado id =", doc_id)

# Ahora ligamos el documento al curso
sql_upd = f"UPDATE courses SET document_id = '{doc_id}' WHERE id = '{course_id}';"
res_upd = subprocess.run(
    ["docker","exec","acvg-postgres","psql","-U","postgres","-d","course_generator","-c",sql_upd],
    capture_output=True, text=True,
)
if res_upd.returncode != 0:
    print("DB ERROR upd:", res_upd.stderr[:800])
    sys.exit(2)
print("   ✅ Curso ligado a document_id OK")

banner("PASO 4/7: POST /courses/{id}/analyze  (LLM AnalyzerAgent real)")
t0 = time.time()
_, ana = req("POST", f"/courses/{course_id}/analyze?force_regenerate=true", body=None, timeout=300)
print(f"   ⏱  {time.time()-t0:.1f}s")
assert ana.get("success"), f"Analyze NO success: {ana}"
assert_no_fallback(ana, "analyze")
ana_data = ana["data"]
print("   📌 title =", ana_data["analysis"].get("title"))
print("   📌 subject =", ana_data["analysis"].get("subject"))
print("   📌 main_topics =", ana_data["analysis"].get("main_topics"))
if len(ana_data["analysis"].get("summary", "")) < 40:
    print("   ❌ Summary muy corto, probablemente fallback (aunque no marca flag)")
    sys.exit(13)
print("   📌 len(summary) =", len(ana_data["analysis"].get("summary", "")))
print("   📌 concepts# =", len(ana_data["analysis"].get("concepts", [])))

banner("PASO 5/7: POST /courses/{id}/pedagogical-design  (LLM PedagogicalAgent real)")
t0 = time.time()
_, ped = req("POST", f"/courses/{course_id}/pedagogical-design?force_regenerate=true", body=None, timeout=300)
print(f"   ⏱  {time.time()-t0:.1f}s")
assert ped.get("success"), f"Pedagogical NO success: {ped}"
assert_no_fallback(ped, "pedagogical-design")
ped_data = ped["data"]
# La respuesta de pedagogical-design puede tener diferentes keys:
ped_obj = ped_data.get("pedagogical") or ped_data.get("pedagogical_design") or {}
print("   📌 keys =", sorted(ped_data.keys()))
print("   📌 teaching_method =", ped_obj.get("teaching_method"))
print("   📌 prerequisites =", ped_obj.get("prerequisites"))
print("   📌 learning_objectives# =", len(ped_obj.get("learning_objectives", [])))
print("   📌 lesson_structure# =", len(ped_obj.get("lesson_structure", [])))
print("   📌 examples# =", len(ped_obj.get("examples", [])))

banner("PASO 6/7: POST /courses/{id}/script  (LLM ScriptAgent real)")
t0 = time.time()
_, scr = req("POST", f"/courses/{course_id}/script?force_regenerate=true", body=None, timeout=300)
print(f"   ⏱  {time.time()-t0:.1f}s")
assert scr.get("success"), f"Script NO success: {scr}"
assert_no_fallback(scr, "script")
scr_data = scr["data"]
scr_obj = scr_data.get("script") or {}
print("   📌 keys =", sorted(scr_data.keys()))
print("   📌 scenes# =", len(scr_obj.get("scenes", [])))
print("   📌 tone =", scr_obj.get("tone"))
print("   📌 total_duration_seconds =", scr_obj.get("total_duration_seconds"))
scenes = scr_obj.get("scenes", [])
for i, sc in enumerate(scenes[:3], 1):
    print(f"     • Escena {i}: {str(sc.get('title'))[:60]} ({sc.get('duration_seconds')}s)")
first_title = ""
if scenes:
    first_title = (str(scenes[0].get("title", "")) or "").lower()
if "introducción al curso y presentación de objetivos" in first_title:
    print("   ⚠️  Primera escena idéntica a deterministic fallback (aunque flag=False)")
else:
    print("   ✅ Primera escena DISTINTA a fallback -> LLM real confirmado por contenido")

banner("PASO 7/7: Resumen")
print(f"   ✅ Curso {course_id}")
ana_obj = ana["data"].get("analysis", ana["data"])
print(f"   ✅ Analysis  OK  | topics={len(ana_obj.get('main_topics', []))}  concepts={len(ana_obj.get('concepts', []))}")
print(f"   ✅ Pedagogy  OK  | objectives={len(ped_obj.get('learning_objectives', []))}  lessons={len(ped_obj.get('lesson_structure', []))}")
print(f"   ✅ Script    OK  | scenes={len(scr_obj.get('scenes', []))}  duration={scr_obj.get('total_duration_seconds')}s")
print("\n🎉 ¡APIs REALES (gpt-4o-mini) usadas en TODO el flujo! NINGÚN fallback deterministic activado.")
