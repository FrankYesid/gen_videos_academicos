# 0.5.0 - FASE 4 - Pedagogical Agent ✅ COMPLETED
## Added
- Enhanced pedagogical schemas (PedagogicalOutput, LessonStructureItem, Example, CommonMistake)
- Comprehensive pedagogical prompt template with instructional design guidelines
- PedagogicalAgent implementation for learning design
- Pedagogical API routes (POST /api/v1/pedagogical/courses/{id}, GET /api/v1/pedagogical/courses/{id})
- Integrated pedagogical design into course workflow via courses API
- Teaching strategies and assessment methods in pedagogical output
- Lesson structure with duration estimation and purpose
- Enhanced mock service with pedagogical mock data
- Course workflow integration with pedagogical design status
## Modified
- Enhanced openai_service.py mock with pedagogical output support
- Updated courses API with integrated pedagogical design endpoint
- Enhanced course workflow with PEDAGOGICAL_DESIGN status
- Added pedagogical router to main API router
## Technical Implementation
- Instructional design principles in prompt (Bloom's Taxonomy, ADDIE, UDL)
- Structured lesson breakdown with modules and topics
- Learning objectives using SMART criteria
- Teaching strategies and assessment methods
- Common mistake identification and correction
- Activity suggestions for engagement
- Duration estimation based on content complexity
## Validation
- ✅ Pedagogical schemas with comprehensive fields
- ✅ Pedagogical prompt template with instructional design guidelines
- ✅ Pedagogical agent implementation
- ✅ Pedagogical API routes 
- ✅ Workflow integration with course status management
- ✅ Mock service support for testing

# 0.4.0 - FASE 3 - Analyzer Agent ✅ COMPLETED
## Added
- OpenAI service with structured outputs using JSON Schema
- MockOpenAIService for testing without API calls
- BaseAgent abstract class with common agent functionality
- AnalyzerAgent implementation for document analysis
- Analysis schemas (AnalysisOutput, Concept, Analysis, AnalysisCreate)
- Analyzer prompt template with academic content analysis guidelines
- Agent execution logging with AgentRun model tracking
- Analysis API routes (POST /api/v1/analysis/courses/{id}, GET /api/v1/analysis/courses/{id})
- Automatic course updates with analysis results
- Structured JSON Schema integration with OpenAI API
- Error handling and retry logic with tenacity
## Modified
- Updated requirements.txt to include openai==1.45.0
- Enhanced config.py with OpenAI configuration parameters
- Updated agent execution to use utcnow() for consistent timestamps
- Added analysis router to main API router
- Enhanced Course model with error_message field
## Technical Implementation
- Structured outputs using OpenAI's json_schema format
- Agent execution tracking with start/end times and status
- Automatic course metadata population from analysis results
- Mock service fallback when OPENAI_API_KEY not configured
- Comprehensive prompt engineering for academic content analysis
## Validation
- ✅ OpenAI service implementation with structured outputs
- ✅ Base agent class with execution logging
- ✅ Analyzer agent with analysis schema
- ✅ Analysis prompt template creation
- ✅ Analysis API routes implementation
- ✅ Agent execution logging framework
- ✅ Course integration with analysis results
- ✅ Mock service for testing without API keys

# 0.3.0 - FASE 2 - PDF Pipeline ✅ COMPLETED
## Added
- Alembic database migrations system with env.py, script.py.mako
- Initial migration creating all tables (documents, courses, lessons, scenes, videos, agent_runs)
- PDF upload endpoint POST /api/v1/documents with multipart/form-data support
- File validation logic (extension .pdf, MIME type application/pdf, max size 50MB)
- StorageService with SHA-256 based file deduplication
- ExtractionService using PyMuPDF for text extraction from PDFs
- DocumentService with full upload workflow and course creation
- Custom JSON encoder for UUID and datetime serialization
- Document API routes: upload, list, get details, delete
- Course integration with document upload workflow
- Automatic text extraction during upload pipeline
- File deduplication based on SHA-256 hash
- Error handling for corrupt/empty PDFs and missing text
## Modified
- Updated database.py to use Alembic migrations instead of auto-create
- Enhanced security.py with CustomJSONResponse and CustomJSONEncoder
- Updated main.py to use custom JSON response class
- Added database volume to docker-compose.yml for persistence
- Enhanced document_service.py with CourseService import
## Validation
- ✅ Database migrations applied successfully
- ✅ PDF upload endpoint working (POST /api/v1/documents)
- ✅ File validation functioning (extension, MIME type, size)
- ✅ Text extraction working with PyMuPDF
- ✅ Document and course creation pipeline working
- ✅ SHA-256 based file deduplication working
- ✅ Custom JSON serialization for UUID/datetime working
- ✅ API endpoints responding correctly (list, get, delete)
- ✅ Error handling for invalid files working
- ✅ All services remain healthy after Phase 2 implementation

# 0.2.0 - FASE 1 - Foundation ✅ COMPLETED
## Added
- Estructura completa de directorios backend/frontend/database/storage/docs/tests
- docker-compose.yml con 4 servicios: postgres, redis, backend, frontend (healthchecks incluidos)
- .env.example con todas las variables de entorno
- .gitignore exhaustivo
- Makefile con comandos: install, dev, build, up, down, test, lint, format, clean
- PLAN.md con arquitectura completa, dependencias, DB schema, API, agentes, fases
- Backend FastAPI con módulos core (config, database, logging, security, exceptions)
- API router versionado /api/v1 con endpoint health
- Frontend React + TypeScript + Vite + TailwindCSS con estructura base
- Componentes frontend base: FileUploader, CourseCard, AnalysisViewer, etc.
- Servicios API frontend con configuración axios
- Tipos TypeScript para document, course, analysis, video
- Modelos SQLAlchemy: document, course, lesson, scene, video, agent_run
- Schemas Pydantic para validación de datos
- Servicios backend: document_service, extraction_service, storage_service, course_service
- Tests structure: unit, integration, e2e
- Dockerfiles para backend y frontend
- README.md con documentación completa del proyecto
## Validation
- ✅ All 4 Docker services healthy (postgres, redis, backend, frontend)
- ✅ Health endpoint responding correctly at /api/v1/health
- ✅ Services accessible on expected ports (5432, 6379, 8000, 5173)
- ✅ Docker Compose setup functional
- ✅ Backend FastAPI application running with core modules
- ✅ Frontend React application serving on port 5173
- ✅ Database connectivity established
- ✅ Redis connectivity established

# 0.1.0
## Added
- PROJECT_SPECIFICATION_AI_COURSE_VIDEO_GENERATOR.txt (especificación maestra)
