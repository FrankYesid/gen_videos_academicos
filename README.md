# AI Course Video Generator

> Plataforma Full Stack que transforma PDFs académicos en videos educativos utilizando Inteligencia Artificial.

[![Phase](https://img.shields.io/badge/Phase-FASE%201-Foundation-blue)](#)
[![Status](https://img.shields.io/badge/Status-WIP-orange)](#)
[![License](https://img.shields.io/badge/License-MIT-green)](#)

---

## 1. Descripción

Permite que un usuario cargue un archivo PDF con contenido académico y que el sistema transforme automáticamente ese contenido en una clase educativa en video:

```
PDF
→ Extracción de contenido
→ Analyzer Agent (OpenAI)
→ Pedagogical Agent
→ Script Agent
→ Aprobación del usuario
→ Video Agent → HeyGen API
→ Webhook + QA
→ Video final
```

### Características

- Subida de PDF con Drag & Drop
- Extracción automática de texto (PyMuPDF)
- 5 agentes de IA especializados (Structured Outputs)
- Diseño pedagógico estructurado
- Generación de guion con escenas
- Aprobación manual del guion antes de generar video
- Integración HeyGen (Template API + Video Agent + **Mock Provider**)
- Webhooks para actualizaciones de estado
- Control de calidad automático (QA Agent)
- Historial de cursos
- Procesamiento asíncrono (Redis + Celery)
- Tests unitarios, integración y E2E

---

## 2. Arquitectura

```
┌─────────────┐     REST API      ┌────────────────────────────┐
│   FRONTEND  │ ────────────────> │         BACKEND            │
│  React/TS   │                   │  FastAPI + SQLAlchemy      │
│  Vite/TW    │                   │  Celery (async workers)    │
└─────────────┘                   └───────┬──────────┬─────────┘
                                          │          │
                         ┌────────────────┴───┐  ┌───┴──────────────────┐
                         │   PostgreSQL 16    │  │     Redis 7          │
                         │   (Persistencia)   │  │   (Queue / Cache)    │
                         └────────────────────┘  └───┬──────────────────┘
                                                      │
                                         ┌────────────┴────────────┐
                                         │                         │
                                         v                         v
                                    OpenAI API              HeyGen API
                                 (Structured Outputs)    (Video Generation)
```

### Servicios (Fase 1)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `frontend` | 5173 | React + Vite + Tailwind |
| `backend` | 8000 | FastAPI + Uvicorn |
| `postgres` | 5432 | Base de datos |
| `redis` | 6379 | Cola / Cache |

---

## 3. Requisitos

- **Docker Desktop 4.30+** con Docker Compose v2
- **Python 3.12+** (solo para desarrollo local sin Docker)
- **Node.js 20+** (solo para desarrollo local sin Docker)
- **Make** (opcional, para comandos del Makefile)

### Cuentas externas (producción)

| Servicio | Propósito | Variable |
|----------|-----------|----------|
| OpenAI | Agentes IA | `OPENAI_API_KEY` |
| HeyGen | Generación de video | `HEYGEN_API_KEY` |

> ⚠️ En `HEYGEN_MODE=mock` **no se consume créditos reales**.

---

## 4. Instalación rápida (Docker recomendado)

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Editar .env y agregar API keys (opcional en FASE 1)

# 3. Levantar toda la plataforma
docker compose up --build

# Esperar a que todos los healthchecks pasen
docker compose ps
```

Servicios disponibles cuando los contenedores estén `healthy`:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health check**: http://localhost:8000/api/v1/health
- **Postgres**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 5. Instalación local (sin Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

Requiere PostgreSQL y Redis ejecutándose localmente.

---

## 6. Variables de entorno

Archivo: `.env` (copia de `.env.example`)

### Aplicación
| Variable | Default | Descripción |
|----------|---------|-------------|
| `APP_ENV` | `development` | Entorno: development/production |
| `BACKEND_PORT` | `8000` | Puerto API |
| `FRONTEND_PORT` | `5173` | Puerto frontend |

### Base de datos
| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql://postgres:postgres@postgres:5432/course_generator` |

### OpenAI
| Variable | Default | Descripción |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `""` | Tu API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo para agentes |
| `OPENAI_TEMPERATURE` | `0.2` | Creatividad |

### HeyGen
| Variable | Default | Descripción |
|----------|---------|-------------|
| `HEYGEN_MODE` | `mock` | `mock` / `production` |
| `HEYGEN_API_KEY` | `""` | API key HeyGen |
| `HEYGEN_AVATAR_ID` | `""` | Avatar por defecto |
| `HEYGEN_VOICE_ID` | `""` | Voz por defecto |
| `HEYGEN_TEMPLATE_ID` | `""` | Template por defecto |
| `HEYGEN_WEBHOOK_SECRET` | `""` | Firma webhook |

### Upload & QA
| Variable | Default |
|----------|---------|
| `MAX_FILE_SIZE_MB` | `50` |
| `DEFAULT_LANGUAGE` | `es` |
| `DEFAULT_DURATION_MINUTES` | `10` |
| `QA_MIN_SCORE` | `80` | Score mínimo para aprobar QA |

---

## 7. Ejecución

### Comandos Makefile
```bash
make dev            # docker compose up --build
make up             # docker compose up -d --build
make down           # docker compose down
make logs           # Seguir logs
make ps             # Estado servicios

make install        # Instalar deps locales (pip + npm)
make backend-dev    # Backend local
make frontend-dev   # Frontend local

make test           # Tests unit + integración
make test-unit      # Tests unitarios backend
make test-integration
make test-e2e       # Playwright E2E
make test-backend
make test-frontend

make lint           # Ruff + ESLint
make format         # Formatear código
make build          # Build imágenes
make clean          # Limpiar caches
make reset          # Borrar contenedores + volúmenes
```

### Comandos Docker Compose
```bash
docker compose up --build            # Levantar todo + logs
docker compose up -d --build         # Levantar todo (background)
docker compose logs -f [servicio]    # Logs
docker compose exec backend bash     # Shell en backend
docker compose exec frontend sh      # Shell en frontend
docker compose down -v               # Todo abajo + volúmenes (borra DB!)
```

---

## 8. API REST

### Prefijo: `/api/v1`

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check ✅ FASE 1 |
| `POST` | `/documents` | Subir PDF (multipart) |
| `GET` | `/documents` | Listar documentos |
| `GET` | `/documents/{id}` | Obtener documento |
| `POST` | `/courses` | Crear curso |
| `GET` | `/courses` | Listar cursos (historial) |
| `GET` | `/courses/{id}` | Detalle |
| `POST` | `/courses/{id}/analyze` | Lanzar Analyzer Agent |
| `GET` | `/courses/{id}/analysis` | Ver análisis |
| `POST` | `/courses/{id}/generate-script` | Generar guion |
| `GET` | `/courses/{id}/script` | Obtener guion |
| `POST` | `/courses/{id}/approve-script` | Aprobar guion |
| `POST` | `/courses/{id}/generate-video` | Generar video (202) |
| `GET` | `/courses/{id}/status` | Estado + progreso |
| `GET` | `/courses/{id}/video` | Video final |
| `POST` | `/webhooks/heygen` | Webhook HeyGen |

### Health check (ejemplo)
```bash
curl -s http://localhost:8000/api/v1/health | jq
```
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "0.2.0",
    "service": "ai-course-video-generator",
    "timestamp": "2025-08-22T...Z"
  },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

## 9. Workflow de Estados

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> UPLOADED: PDF guardado
    UPLOADED --> EXTRACTING: Extraer texto
    EXTRACTING --> ANALYZING: AnalyzerAgent
    ANALYZING --> PEDAGOGICAL_DESIGN: PedagogicalAgent
    PEDAGOGICAL_DESIGN --> SCRIPT_GENERATED: ScriptAgent
    SCRIPT_GENERATED --> SCRIPT_VALIDATED: Usuario aprueba
    SCRIPT_VALIDATED --> VIDEO_GENERATING: HeyGen create
    VIDEO_GENERATING --> VIDEO_PROCESSING: HeyGen rendering
    VIDEO_PROCESSING --> VIDEO_READY: Webhook completed
    VIDEO_READY --> QA: QAAgent
    QA --> COMPLETED: Score >= QA_MIN_SCORE
    QA --> SCRIPT_GENERATED: Rechazado / regenerar
    ANY_STATE --> FAILED: Error
    FAILED --> UPLOADED: Reintentar
    COMPLETED --> [*]
```

---

## 10. Agentes

| Agente | Archivo | Propósito |
|--------|---------|-----------|
| AnalyzerAgent | `backend/app/agents/analyzer_agent.py` | Extraer temas, conceptos, objetivos del texto |
| PedagogicalAgent | `backend/app/agents/pedagogical_agent.py` | Diseñar estructura pedagógica |
| ScriptAgent | `backend/app/agents/script_agent.py` | Generar escenas con narración y visuales |
| VideoAgent | `backend/app/agents/video_agent.py` | Adaptar guion al VideoProvider |
| QAAgent | `backend/app/agents/qa_agent.py` | Validar calidad del video final |

Todos los agentes:
- Usan **Structured Outputs** de OpenAI (JSON Schema)
- Salidas validadas con **Pydantic**
- Prompts versionados en `backend/app/prompts/*.txt`
- Ejecuciones registradas en tabla `agent_runs`

---

## 11. Integración HeyGen

### Estrategias soportadas

| Provider | Clase | Modo |
|----------|-------|------|
| **Mock** | `MockVideoProvider` | Desarrollo / Testing |
| **Video Agent** | `HeyGenVideoAgentProvider` | Automatización alta |
| **Template API** | `HeyGenTemplateProvider` | Control por escenas |

```python
# Selección por variable de entorno
# HEYGEN_MODE=mock   → MockVideoProvider (sin costo)
# HEYGEN_MODE=production  → HeyGenVideoAgentProvider / Template
```

### Mock Provider
Simula todo el ciclo: `created → processing → completed` en ~10s, devuelve un recurso demo. Útil para tests y desarrollo sin gastar créditos.

---

## 12. OpenAI

Flujo estricto (evita parseo frágil):
```
LLM → Structured Output (json_schema) → Pydantic → Database
```

**Nunca** depender de texto libre para salidas que deben procesarse por código.

---

## 13. Docker

### Construcción individual
```bash
docker build -t acvg-backend ./backend
docker build -t acvg-frontend ./frontend
```

### Healthchecks
Cada servicio define healthcheck en `docker-compose.yml`. Espera a:
- **Postgres**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Backend**: `GET /api/v1/health` → 200
- **Frontend**: HTTP 200 en puerto 5173

### Volúmenes
- `postgres_data`: Persistencia de datos DB
- `redis_data`: Cache/queue de Redis
- Bind mounts: `./backend`, `./frontend/src` → hot reload en desarrollo

---

## 14. Testing

```bash
# Backend (FASE 1: solo estructura)
cd backend && python -m pytest tests/ -v

# Frontend unit
cd frontend && npm run test

# E2E con Playwright
cd frontend && npm run test:e2e

# Todo via Makefile
make test           # unit + integration
make test-e2e       # E2E
```

### Modo Mock
Por defecto `HEYGEN_MODE=mock`, así que `pytest` se ejecuta **sin consumir créditos reales**.

Para ejecutar tests contra HeyGen real:
```bash
RUN_EXTERNAL_TESTS=true pytest tests/integration/test_heygen_real.py -v
```

---

## 15. Fases de implementación

| # | Fase | Estado | Descripción |
|---|------|--------|-------------|
| 1 | **Foundation** | ✅ Actual | Estructura, Docker, Backend/Frontend base, Health |
| 2 | PDF Pipeline | ⏳ Pendiente | Upload, validación, extracción, tablas DB |
| 3 | Analyzer Agent | ⏳ Pendiente | OpenAI + schema analyzer |
| 4 | Pedagogical Agent | ⏳ Pendiente | Objetivos / estructura lección |
| 5 | Script Agent | ⏳ Pendiente | Escenas + narración |
| 6 | Frontend Pages | ⏳ Pendiente | Funcionalidad real de páginas |
| 7 | HeyGen | ⏳ Pendiente | HeyGenService + 3 providers |
| 8 | Full Workflow | ⏳ Pendiente | Orquestación + async workers |
| 9 | QA Agent | ⏳ Pendiente | Scoring final |
| 10 | Testing Suite | ⏳ Pendiente | Unit / Integration / E2E |
| 11 | Documentation | ⏳ Pendiente | Docs completas + diagramas |

---

## 16. Troubleshooting

| Problema | Solución |
|----------|----------|
| Healthcheck backend falla | Revisar logs: `docker compose logs backend` |
| Frontend no se conecta al API | Ver `VITE_API_BASE_URL` (en prod debe ser la URL pública) |
| PostgreSQL `connection refused` | Esperar a que `postgres` esté `healthy` |
| `module not found` en Python | `docker compose build --no-cache backend` |
| `npm install` lento en contenedor | Aumentar memoria Docker Desktop |
| Puerto 5432/6379/8000/5173 ocupado | Cambiar puertos en `.env` |
| `ModuleNotFoundError: No module named 'app'` | Asegurarte de ejecutar desde `backend/` |

### Logs útiles
```bash
# Todo
docker compose logs -f --tail=100

# Solo backend
docker compose logs -f backend --tail=100

# Base de datos
docker compose logs postgres
```

---

## 17. Estructura del proyecto

```
ai-course-video-generator/
├── backend/                FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── main.py         Entrypoint
│   │   ├── api/            Rutas versionadas /api/v1
│   │   ├── agents/         5 agentes IA
│   │   ├── services/       Lógica de negocio (Document, OpenAI, HeyGen...)
│   │   ├── models/         Tablas SQLAlchemy
│   │   ├── schemas/        Schemas Pydantic
│   │   ├── prompts/        Prompts .txt versionados
│   │   ├── core/           Config, DB, Logging, Security, Exceptions
│   │   └── workers/        Tareas asíncronas (Celery)
│   ├── tests/              unit / integration / e2e
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               React 18 + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── pages/          Dashboard / Upload / Analysis / Script / Video
│   │   ├── components/     10+ componentes reutilizables
│   │   ├── services/       API layer (Axios)
│   │   ├── hooks/          TanStack Query
│   │   ├── types/          TypeScript interfaces
│   │   └── utils/          Helpers
│   ├── tests/
│   ├── Dockerfile
│   └── package.json
├── database/               Alembic migrations + seed
├── storage/                PDFs / scripts / videos
├── tests/                  Fixtures y tests cross-stack
├── docs/                   Arquitectura, API, Agentes, Setup, Testing, Deployment
├── scripts/                setup.sh, dev.sh, test.sh, reset.sh
├── docker-compose.yml      4 servicios con healthchecks
├── Makefile                ~20 comandos
├── .env.example
├── PROJECT_SPECIFICATION.md
├── PLAN.md
├── CHANGELOG.md
└── README.md
```

---

## 18. Contribuir (FASE actual)

La FASE 1 es fundacional. Para contribuir en la siguiente fase lee `PLAN.md` y la especificación en `PROJECT_SPECIFICATION_AI_COURSE_VIDEO_GENERATOR.txt`.

---

## 19. Licencia

MIT — Ver archivo `LICENSE`.
