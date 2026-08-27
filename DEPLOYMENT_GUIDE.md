# Guía de Despliegue - AI Course Video Generator (ACVG)

> **Estado de validación Docker actual (2026-08-23):** Todo el stack verificado E2E en Docker Desktop: `health → create course → workflow/process → final_status=COMPLETED, progress=100, qa score=90 approved, video=COMPLETED (mock)`. 113 tests unit+integration PASSED.

---

## 0. Arquitectura de Servicios (4 contenedores)

```
┌───────────────────────────────────────────────────────────────┐
│                    Docker Compose - acvg-net                  │
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  postgres:16 │   │  redis:7     │   │  backend:8000    │   │
│  │ (puerto 5432)│   │ (puerto 6379)│   │ FastAPI + Alembic│   │
│  │  (persiste)  │   │  (persiste)  │◄──┤  Python 3.12     │   │
│  └──────┬───────┘   └──────────────┘   │  (workers Celery) │   │
│         │                              └────────┬─────────┘   │
│         │                                       │             │
│         └───────────────────┬───────────────────┘             │
│                             │                                 │
│                   ┌─────────▼──────────┐                      │
│                   │  frontend:5173     │                      │
│                   │  React 18 + Vite   │                      │
│                   │  (público: WEB UI) │                      │
│                   └────────────────────┘                      │
└───────────────────────────────────────────────────────────────┘
```

| Servicio | Imagen | Host Puerto | Health URL |
|----------|--------|-------------|------------|
| acvg-postgres | postgres:16-alpine | 5432 | `pg_isready` |
| acvg-redis | redis:7-alpine | 6379 | `redis-cli ping` |
| acvg-backend | custom (python:3.12-slim) | 8000 | http://localhost:8000/api/v1/health |
| acvg-frontend | custom (node:20-alpine) | 5173 | http://localhost:5173 |

---

## 1. Prerrequisitos (Obligatorios)

| Software | Versión mínima | Verificación |
|----------|---------------|--------------|
| Docker Desktop | 4.30+ (engine 27.x) | `docker version` (debe mostrar Server Version) |
| Docker Compose v2 | integrado en Desktop | `docker compose version` |
| Git | cualquier | `git --version` |
| **Memoria RAM** | ≥ 6 GB libres | Docker Desktop → Settings → Resources |
| **Disco** | ≥ 4 GB libres | (imágenes python/node + 371 npm + 70 paquetes pip) |

> **NO necesitas** Python, Node, PostgreSQL ni Redis locales — todo corre en contenedores.

---

## 2. Despliegue Paso a Paso (Primera Vez)

### 2.1. Clonar repositorio

```bash
git clone <TU_REPO_URL> gen_videos_academicos
cd gen_videos_academicos
```

### 2.2. Configurar variables de entorno

```bash
# Copiar plantilla (solo si no existe .env aún)
cp .env.example .env
```

Edita `./.env` y rellena **solo lo que necesites cambiar**. Los defaults funcionan en MOCK mode:

```dotenv
# ---- Para MODO MOCK (sin APIs de pago) ----
HEYGEN_MODE=mock            # deja así para no gastar créditos
OPENAI_API_KEY=             # se puede dejar vacío → usa MockOpenAIService (QA score=90)

# ---- Cambia a PRODUCCIÓN cuando tengas keys ----
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
# HEYGEN_MODE=production
# HEYGEN_API_KEY=xxxxxxxxxx
# HEYGEN_AVATAR_ID=xxxxxxx
# HEYGEN_VOICE_ID=es-XXXX
```

Referencia completa en: [.env.example](file:///d:/GitHub/gen_videos_academicos/.env.example)

### 2.3. Levantar TODOS los servicios + Build

```powershell
# (Windows PowerShell como administrador o usuario normal con Docker Desktop arrancado)
docker compose up -d --build
```

Esto hace internamente:
1. Build de `backend/Dockerfile` → instala requirements.txt (70 paquetes pip, ~100s)
2. Build de `frontend/Dockerfile` → npm install (371 paquetes, ~280s)
3. Crea volúmenes persistentes `postgres_data` y `redis_data`
4. Espera a que `postgres` y `redis` estén **healthy** → arranca `backend`
5. Espera a que `backend` esté **healthy** (`/api/v1/health` → 200) → arranca `frontend`

### 2.4. Verificar estado de los 4 contenedores

```bash
docker compose ps
# Salida esperada: 4 servicios con STATE=running STATUS=healthy
#
#   acvg-backend    backend    running   Up 1m (healthy)
#   acvg-frontend   frontend   running   Up 1m (healthy)
#   acvg-postgres   postgres   running   Up 1m (healthy)
#   acvg-redis      redis      running   Up 1m (healthy)
```

Si tarda, sigue logs en vivo:
```bash
docker compose logs -f --tail=50
```

### 2.5. Aplicar migraciones de base de datos (PASO OBLIGATORIO)

```bash
docker compose exec backend alembic upgrade head
# Salida esperada:
# Running upgrade  -> 001, Initial migration
# Running upgrade 001 -> 002, Add analysis JSONB fields to courses
# Running upgrade 002 -> 003, add_course_script_and_qa_fields
# Running upgrade 003 -> 004, fix_course_document_id_nullable
# Running upgrade 004 -> 005, agent_runs + lessons + scenes + videos fix
```

Luego valida 5 migraciones HEAD y 7 tablas creadas:
```bash
# Alembic current
docker compose exec backend alembic current
# → 005 (head)

# Ver tablas PostgreSQL
docker compose exec postgres psql -U postgres -d course_generator -c "\dt"
# → 7 filas: agent_runs, alembic_version, courses, documents, lessons, scenes, videos
```

### 2.6. Verificar endpoints

```powershell
# 1) Backend Health
Invoke-RestMethod http://localhost:8000/api/v1/health
# → success=True, data.status="ok", data.version="0.2.0"

# 2) Frontend (abre navegador):
Start-Process "http://localhost:5173"

# 3) Swagger / OpenAPI Docs (interactivo):
Start-Process "http://localhost:8000/docs"
```

### 2.7. Smoke Test E2E (Opcional pero recomendado)

Prueba el workflow **end-to-end completo** en MODO MOCK (sin gastar créditos). Genera curso, análisis, diseño pedagógico, guion, video (mock) y QA (mock).

```powershell
# --- Paso A: Crear curso vacío ---
$body = @{ title = "Curso Smoke E2E"; subject = "Testing"; level = "beginner"; language = "es" } | ConvertTo-Json
$c = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/courses" -Method Post -Body $body -ContentType "application/json"
$cid = $c.data.id
Write-Host "Curso creado: id=$cid status=$($c.data.status)"

# --- Paso B: Ejecutar pipeline completo (SYNC, ~15s en modo mock) ---
$opts = @{ provider="mock"; skip_qa=$false; auto_approve_script=$true; run_async=$false } | ConvertTo-Json
$r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/workflow/courses/$cid/process" -Method Post -Body $opts -ContentType "application/json"
Write-Host "RESULTADO: status=$($r.data.final_status) progress=$($r.data.final_progress) steps=$($r.data.steps_completed -join ',')"

# Salida ESPERADA ✅:
#   RESULTADO: status=COMPLETED progress=100 steps=analysis, pedagogical_design, script, script_approved, video_generate, qa

# --- Paso C: Verificar artefactos finales (video + QA) ---
$s = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/courses/$cid/status" -Method Get
$s | ConvertTo-Json -Depth 8
# → data.status = "COMPLETED"
# → data.video.status = "COMPLETED", video_url, thumbnail_url, duration presentes
# → data.qa.status = "approved", qa.score = 90
```

---

## 3. Rutas API Implementadas (Base: `/api/v1`)

| Módulo | Método | Ruta | Descripción |
|--------|--------|------|-------------|
| Health | GET | `/health` | Liveness/readiness |
| **Documents** | POST | `/documents` | Subir PDF + crear curso opcional |
| | GET | `/documents` | Listar documentos subidos |
| | GET | `/documents/{id}` | Descargar metadata documento |
| | DELETE | `/documents/{id}` | Eliminar documento |
| **Courses** | POST | `/courses` | Crear curso manualmente |
| | GET | `/courses` | Historial de cursos (paginado: skip/limit) |
| | GET | `/courses/{id}` | Detalle completo del curso |
| | PATCH | `/courses/{id}` | Actualizar título/status/progress/etc |
| | DELETE | `/courses/{id}` | Eliminar curso + cascade lessons/scenes/videos |
| | GET | `/courses/{id}/status` | Status + progress + video + QA (para dashboard) |
| | POST | `/courses/{id}/analysis` | Trigger análisis |
| | GET | `/courses/{id}/analysis` | Obtener análisis guardado |
| | POST | `/courses/{id}/pedagogical` | Trigger diseño pedagógico |
| | GET | `/courses/{id}/pedagogical` | Obtener diseño pedagógico |
| | POST | `/courses/{id}/script` | Guardar/actualizar guion JSONB scenes |
| | GET | `/courses/{id}/script` | Obtener guion + scenes |
| | POST | `/courses/{id}/generate-video` | Disparar generación video al provider |
| | POST | `/courses/{id}/qa-review` | Disparar revisión QA |
| | GET | `/courses/{id}/qa` | Obtener resultado QA |
| Analysis | POST | `/analysis/courses/{id}` | Trigger análisis force |
| | GET | `/analysis/courses/{id}` | Get análisis |
| Pedagogical | POST | `/pedagogical/courses/{id}` | Trigger regenerate |
| | GET | `/pedagogical/courses/{id}` | Get diseño pedagógico |
| Script | POST | `/script/courses/{id}` | Bulk create scenes + script |
| | GET | `/script/courses/{id}` | Get scenes script |
| Videos | POST | `/videos/generate` | Generar video (lesson_id) |
| | GET | `/videos/status/{video_id}` | Poll estado generación |
| | GET | `/videos/latest/{course_id}` | Último video generado del curso |
| QA | POST | `/qa/review` | Iniciar revisión QA |
| | GET | `/qa/courses/{id}` | Obtener resultado QA |
| **Workflow ⭐** | **POST** | **`/workflow/courses/{id}/process`** | **Pipeline E2E completo: analysis → pedag → script → approve → video → qa** |
| | GET | `/workflow/courses/{id}/status` | Estado por step del pipeline |

### Formato estándar de respuesta TODOS los endpoints

Siempre 200-299 si llegó a la capa FastAPI; la estructura es **uniforme**:
```json
{
  "success": true | false,
  "data":    { ... } | null,
  "error":   { "code": "...", "message": "...", "details": ... } | null,
  "meta":    { "request_id": "uuid", "timestamp": "2026-08-...", "pagination?": {...} }
}
```

### Body del endpoint Workflow `/workflow/courses/{id}/process` (POST)

```json
{
  "provider":             "mock",        // "mock" (gratis) | "heygen_agent" | "heygen_template"
  "skip_qa":              false,         // saltarse QA y pasar directo COMPLETED (progress=100)
  "auto_approve_script":  true,          // no espera aprobación manual del guion
  "run_async":            false          // false = HTTP 200 al terminar; true = 202 Accepted + BackgroundTasks
}
```

---

## 4. Ciclo de Vida del Proyecto (Comandos Makefile / Docker)

### Con Make (opcional si lo tienes instalado)
```bash
make help              # Ver todos los comandos
make up                # = docker compose up -d --build
make down              # = docker compose down (no borra volúmenes)
make reset             # = docker compose down -v (¡BORRA TODO! datos postgres/redis)
make migrate           # Aplica migraciones
make ps                # docker compose ps
make logs              # docker compose logs -f
make test-backend      # 113 tests
make install           # (solo si trabajas LOCAL sin docker) pip + npm install
```

### Sin Make (directo con docker compose)

| Acción | Comando |
|--------|---------|
| **Arrancar** (build si cambió Dockerfile) | `docker compose up -d --build` |
| **Parar todo** (mantiene datos DB/Redis) | `docker compose down` |
| **Borrar TODO absolutamente** (datos DB + Redis + contenedores + redes) | `docker compose down -v --remove-orphans` |
| **Ver logs en vivo** (todos) | `docker compose logs -f --tail=100` |
| **Logs solo backend** | `docker compose logs -f backend` |
| **Logs solo frontend** | `docker compose logs -f frontend` |
| **Estado contenedores** | `docker compose ps` |
| **Shell interactivo backend** (bash) | `docker compose exec backend /bin/bash` |
| **Ejecutar test unit backend en container** | `docker compose exec backend python -m pytest tests/ -v` |
| **Build frontend producción** (archivos dist/) | `docker compose exec frontend npm run build` |

---

## 5. Modo Mock vs Modo Producción (APIs Reales)

| Feature | MODO MOCK (default `.env`) | MODO PRODUCCIÓN |
|---------|---------------------------|-----------------|
| Requisitos | NINGUNO, 0 costo | OpenAI key + HeyGen key |
| `.env` clave | `HEYGEN_MODE=mock` `OPENAI_API_KEY=` | `HEYGEN_MODE=production` `OPENAI_API_KEY=sk-xxx` `HEYGEN_API_KEY=xxx` |
| Análisis / Pedag / Script | Contenido fijo determinista | Llamada real a OpenAI (JSON Schema structured outputs) |
| Generación Video | URL fake `https://example.com/mock-videos/output.mp4` | HeyGen API real + avatar/voz reales |
| QA | Siempre score=90, approved | Llamada a `gpt-4o-mini` → rubric 8 categorías |
| Tiempo workflow E2E | ~15 segundos | 2–5 minutos (HeyGen tarda en renderizar) |

Cambiar a producción **sin recrear contenedores**:
```bash
# 1. Editar .env (cambiar HEYGEN_MODE, agregar OPENAI_API_KEY + HEYGEN_API_KEY)
# 2. Reiniciar solo backend (el .env se lee al arranque):
docker compose restart backend
```

---

## 6. 5 Migraciones Alembic (orden de aplicación)

| ID | Archivo en `database/migrations/versions/` | Cambio |
|----|-------------------------------------------|--------|
| **001** | `20260822_200000_initial_migration_create_all_tables.py` | Crea 7 tablas base (documents, courses, lessons, scenes, videos, agent_runs, alembic_version) |
| **002** | `20260823_002_add_course_analysis_fields.py` | `courses`: JSONB `main_topics`, `prerequisites`, `concepts`, `keywords`, `pedagogical_data` + `estimated_duration_minutes`, `error_message`; `lessons.activity_suggested` |
| **003** | `20260823_003_add_script_and_qa_fields.py` | `courses`: JSONB `script_data`, `qa_data` |
| **004** | `20260823_004_fix_course_document_id_nullable.py` | `courses.document_id`: `NOT NULL` → `NULL` + FK `ON DELETE SET NULL` |
| **005** | `20260823_005_agent_runs_columns_fix.py` | `agent_runs`: +`model`, `tokens_used`, `created_at`; fix execution_time_ms → BIGINT; started_at nullable; `lessons.title/status NOT NULL default CREATED`; `scenes.educational_purpose → VARCHAR(255)`; `videos`: +`job_id`, +`error_message`, `payload → request_payload` JSONB, `duration → BIGINT`, index `provider_video_id`; todas FK `ON DELETE CASCADE` |

Comandos útiles Alembic (dentro container):
```bash
docker compose exec backend alembic current        # ver migración actual
docker compose exec backend alembic upgrade head   # aplicar todas las pendientes
docker compose exec backend alembic downgrade -1   # volver atrás 1 migración
docker compose exec backend alembic history        # ver historial lineal
```

---

## 7. Troubleshooting (Errores comunes)

### 🔴 Error: `Cannot connect to the Docker daemon`

```
Solución: Inicia Docker Desktop manualmente (Windows: menú Inicio → Docker Desktop).
Espera hasta que la ballena esté verde en la bandeja → luego `docker version` debe mostrar
Server Version.
```

### 🔴 `5432 already in use` (Puerto ocupado)

Otra app usa el 5432 (PostgreSQL local instalado). Cambia `.env`:
```dotenv
DATABASE_PORT=5433
```
Y en `docker-compose.yml` la sección ports de postgres a `"5433:5432"`. Luego `docker compose up -d`.

### 🔴 `5173 already in use` (Vite frontend puerto ocupado)

Cambia `.env`: `FRONTEND_PORT=5174` y reinicia: `docker compose up -d --build frontend`

### 🔴 Migración falla o esquema corrupto (último recurso: limpiar todo)

```powershell
# ⚠️ BORRA los datos de PostgreSQL y Redis PERMANENTEMENTE
docker compose down -v --remove-orphans
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

### 🔴 Workflow /process falla → `final_status=FAILED`

1. Lee errores en la respuesta: `$r.data.errors`
2. Lee logs backend: `docker compose logs backend --tail=100`
3. Común por falta de migraciones → vuelve a ejecutar `alembic upgrade head`

### 🔴 `health` de backend tarda > 60s y nunca se pone healthy

```bash
# Ver si Python arrancó correctamente:
docker compose logs backend --tail=50
# Si dice "ModuleNotFoundError: X" →
docker compose build --no-cache backend ; docker compose up -d backend
```

### 🔴 Frontend no puede llamar al backend (CORS / failed to fetch)

Verifica variable `.env`: `CORS_ORIGINS=http://localhost:5173,http://frontend:5173`. Si cambias el puerto del frontend, agrégalo ahí y reinicia `docker compose restart backend`.

---

## 8. Producción (Avanzado)

### 8.1. Build frontend optimizado

```bash
# 1. Genera dist/ optimizado dentro del container frontend
docker compose exec frontend npm run build

# 2. (Opcional) Empaqueta con Nginx: reemplaza frontend/Dockerfile por una imagen
#    multi-stage que sirva dist/ con Nginx (10x más rápido que vite dev server)
```

### 8.2. Variables de entorno obligatorias para producción

```dotenv
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql://user:strong-pass@managed-postgres:5432/acvg_prod
REDIS_URL=redis://managed-redis:6379/0
CORS_ORIGINS=https://tu-dominio.com
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
HEYGEN_MODE=production
HEYGEN_API_KEY=xxxxxxxxxxxxxxxx
HEYGEN_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

### 8.3. HTTPS + Nginx Inverso

Ejemplo mínimo `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    ssl_certificate     /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;

    location /       { proxy_pass http://127.0.0.1:5173;  # Vite build (dist/) servido por Nginx
                       proxy_set_header Host $host; }

    location /api/   { proxy_pass http://127.0.0.1:8000;
                       proxy_set_header Host $host;
                       proxy_set_header X-Real-IP $remote_addr;
                       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                       proxy_set_header X-Forwarded-Proto $scheme;
                       client_max_body_size 60m; }   # subir PDFs hasta 50MB
}
```

### 8.4. Backups diarios (cronjob)

```bash
# Backup PostgreSQL (ejecuta como tarea programada)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
docker compose exec -T postgres pg_dump -U postgres course_generator | gzip > backups/acvg_${DATE}.sql.gz
# Backup storage (PDFs, videos, thumbnails)
tar czf backups/storage_${DATE}.tar.gz storage/
# Retener 15 días
find backups/ -name "*.gz" -mtime +15 -delete
```

---

## 9. Dónde encontrar más información

| Documento | Ruta |
|-----------|------|
| Plan de implementación 11 fases | [PLAN.md](file:///d:/GitHub/gen_videos_academicos/PLAN.md) §10 tabla + Validation Results |
| Especificación funcional | `PROJECT_SPECIFICATION_AI_COURSE_VIDEO_GENERATOR.txt` |
| Changelog de cambios | `CHANGELOG.md` |
| Archivos migraciones | [database/migrations/versions/](file:///d:/GitHub/gen_videos_academicos/database/migrations/versions/) |
| Rutas backend | [backend/app/api/routes/](file:///d:/GitHub/gen_videos_academicos/backend/app/api/routes/) |
| Rutas /workflow endpoint E2E | [workflow.py](file:///d:/GitHub/gen_videos_academicos/backend/app/api/routes/workflow.py#L535-L588) |
| Modelo Course | [course.py](file:///d:/GitHub/gen_videos_academicos/backend/app/models/course.py#L69-L116) |
| Configuración (Settings) | [config.py](file:///d:/GitHub/gen_videos_academicos/backend/app/core/config.py#L10-L97) |
| Router principal API v1 | [router.py](file:///d:/GitHub/gen_videos_academicos/backend/app/api/router.py#L1-L15) |
| README general | `README.md` |

---

## 10. Checklist Checklist Primer Despliegue (Copy-paste)

- [ ] Docker Desktop corriendo, `docker version` muestra Server Version
- [ ] `.env` creado a partir de `.env.example`
- [ ] `docker compose up -d --build` termina exit code 0
- [ ] `docker compose ps` → 4 containers `STATUS=healthy`
- [ ] `docker compose exec backend alembic upgrade head` → aplica hasta 005 (head)
- [ ] `http://localhost:8000/api/v1/health` → `success: true`
- [ ] `http://localhost:5173` abre Dashboard React
- [ ] `http://localhost:8000/docs` → Swagger UI carga
- [ ] Smoke Test E2E del §2.7 → final_status=`COMPLETED` progress=`100` ✅
- [ ] Opcional: configurar `OPENAI_API_KEY` y `HEYGEN_MODE=production` para APIs reales

---

## 11. Resumen Comandos Rápidos Hoja de Ruta

```powershell
# === SOBRE VIVIENDA (todos los días) ===
docker compose up -d --build         # Arrancar / rebuild si cambió código dockerfile
docker compose ps                    # ¿Están healthy los 4 servicios?
docker compose logs -f backend       # Logs backend (errores workflow)

# === OBLIGATORIO DESPUÉS DE git pull / CAMBIOS EN database/migrations ===
docker compose exec backend alembic upgrade head

# === PRIMERA VEZ / ESQUEMA ROTO / CAMBIO DE BD MAYOR ===
docker compose down -v --remove-orphans     # ⚠️ BORRA TODO
docker compose up -d --build
docker compose exec backend alembic upgrade head

# === PRUEBA DE FUEGO: TODO FUNCIONA ===
#  Crear curso + /workflow/process → debe dar COMPLETED 100
```
