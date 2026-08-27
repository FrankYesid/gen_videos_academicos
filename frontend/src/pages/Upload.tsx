import { useState } from 'react';
import {
  SparklesIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import FileUploader, { FileInfo } from '../components/FileUploader';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import { createCourse } from '../services/courses';
import type { Course, CourseStatus } from '../types/course';

export default function Upload() {
  const { currentCourseId, setCurrentCourse, updateCourseMeta, getRouteForStep } = useCurrentCourse();
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('Ciencias');
  const [level, setLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [language, setLanguage] = useState<'es' | 'en' | 'pt'>('es');
  const [estimatedDuration, setEstimatedDuration] = useState(10);
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);

  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<Course | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleCreate() {
    setCreating(true);
    setErrorMsg(null);
    try {
      const document_id = fileInfo?.document?.id;
      const finalTitle = title.trim() || `Curso ${subject} (${level})`;
      const payload = {
        title: finalTitle,
        subject,
        level,
        language,
        estimated_duration_minutes: estimatedDuration,
        document_id,
      };
      const course = await createCourse(payload);
      setCreated(course);
      setCurrentCourse(course.id, {
        title: course.title,
        status: (course.status as CourseStatus) || 'CREATED',
        progress: course.progress ?? 0,
      });
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail || err?.message || 'No se pudo crear el curso';
      setErrorMsg(typeof detail === 'string' ? detail : 'No se pudo crear el curso');
    } finally {
      setCreating(false);
    }
  }

  function handleRecreate() {
    setCreated(null);
    setTitle('');
    setFileInfo(null);
    setCurrentCourse('' as any);
    updateCourseMeta({ status: null, progress: null, title: null });
  }

  const hasDocument = Boolean(fileInfo?.document?.id);
  const canCreate = !creating && !created && (hasDocument || title.trim() || subject.trim());

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Paso 1 · Subir documento o crear curso
          </h1>
          <p className="text-slate-600 mt-1">
            Sube tu PDF o define un curso manualmente con título, tema y nivel.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge bg-brand-100 text-brand-700">¡Paso 1 de 6!</span>
          {currentCourseId && (
            <button
              type="button"
              onClick={handleRecreate}
              className="btn-secondary btn-sm"
              title="Reinicia el formulario para crear un nuevo curso y actualizar el workflow"
            >
              Nuevo curso
            </button>
          )}
        </div>
      </div>

      {created && (
        <div className="card-step border-emerald-300 bg-gradient-to-br from-emerald-50 to-white">
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
              <CheckCircleIcon className="w-8 h-8 text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold text-emerald-900">
                ¡Curso creado correctamente! 🎉
              </h2>
              <p className="text-emerald-800 text-sm mt-1">
                Título: <strong>{created.title}</strong> · ID:{' '}
                <span className="font-mono text-xs">{created.id}</span> · Estado:{' '}
                <span className="badge bg-emerald-100 text-emerald-700 ml-1">
                  {created.status}
                </span>
              </p>
              {fileInfo?.document && (
                <p className="text-xs text-emerald-700 mt-2">
                  ✅ Documento adjunto: <strong>{fileInfo.name}</strong> ·{' '}
                  {fileInfo.document.page_count ?? '?'} páginas
                </p>
              )}
            </div>
          </div>
          <div className="mt-6">
            <NextStepButton
              overrideLabel="Continuar con el Análisis IA →"
              overrideRoute={getRouteForStep('analysis')}
              description="Identifica automáticamente los temas clave, conceptos, prerrequisitos y objetivos educativos del material"
              size="xl"
              block
              highlight
            />
          </div>
        </div>
      )}

      {errorMsg && !created && (
        <div className="card bg-rose-50 border-rose-300 text-rose-800">
          <p className="font-semibold flex items-center gap-2">
            <InformationCircleIcon className="w-5 h-5" />
            Error al crear el curso
          </p>
          <p className="text-sm mt-1">{errorMsg}</p>
          <p className="text-xs text-rose-600 mt-2">
            Revisa que el backend esté corriendo en el puerto 8000 y ejecuta
            <code className="bg-rose-100 px-1 rounded mx-1">docker compose up -d</code>
            si es necesario.
          </p>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <FileUploader value={fileInfo} onChange={setFileInfo} />

          <div className="card-step border-brand-200 bg-gradient-to-br from-white to-brand-50/30">
            <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-brand-600" />
              Configuración del curso
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="label">Título del curso (opcional)</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Ej: Fundamentos de Álgebra Lineal"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={creating || !!created}
                />
              </div>
              <div>
                <label className="label">Tema / Asignatura</label>
                <input
                  type="text"
                  className="input"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={creating || !!created}
                />
              </div>
              <div>
                <label className="label">Idioma</label>
                <select
                  className="input"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as any)}
                  disabled={creating || !!created}
                >
                  <option value="es">Español</option>
                  <option value="en">English</option>
                  <option value="pt">Português</option>
                </select>
              </div>
              <div>
                <label className="label">Nivel</label>
                <select
                  className="input"
                  value={level}
                  onChange={(e) => setLevel(e.target.value as any)}
                  disabled={creating || !!created}
                >
                  <option value="beginner">Principiante</option>
                  <option value="intermediate">Intermedio</option>
                  <option value="advanced">Avanzado</option>
                </select>
              </div>
              <div>
                <label className="label">Duración objetivo (min)</label>
                <input
                  type="number"
                  className="input"
                  min={1}
                  max={180}
                  value={estimatedDuration}
                  onChange={(e) => setEstimatedDuration(Number(e.target.value))}
                  disabled={creating || !!created}
                />
              </div>
            </div>

            <div className="mt-6">
              {!created && (
                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={!canCreate}
                  className={`btn-upload btn-xl btn-block ${
                    canCreate ? 'pulse-highlight' : ''
                  }`}
                  title="Crea un nuevo curso (con PDF adjunto o solo por título) y guarda el estado actual del workflow"
                >
                  {creating ? (
                    <SparklesIcon className="w-5 h-5 animate-spin" />
                  ) : (
                    <SparklesIcon className="w-5 h-5" />
                  )}
                  <div className="flex flex-col items-start gap-0.5 text-left">
                    <span>
                      {creating
                        ? 'Creando curso en la base de datos...'
                        : hasDocument
                        ? '🚀 Crear curso con PDF adjunto y preparar Análisis'
                        : '🚀 Crear curso (sin PDF) y preparar Análisis'}
                    </span>
                    <span className="text-xs font-normal text-white/85 pl-8">
                      Valida reglas, persiste el curso y activa el botón Continuar → Análisis
                    </span>
                  </div>
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="card bg-amber-50 border-amber-200">
            <h3 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
              <InformationCircleIcon className="w-5 h-5" />
              Requisitos del PDF
            </h3>
            <ul className="text-sm text-amber-800 space-y-1 list-disc list-inside">
              <li>Formato: PDF</li>
              <li>Tamaño máximo: 50 MB</li>
              <li>Contiene texto seleccionable</li>
              <li>Contenido académico claro</li>
            </ul>
          </div>

          <div className="card bg-sky-50 border-sky-200">
            <h3 className="font-semibold text-sky-900 mb-2">Workflow completo</h3>
            <ol className="text-sm text-sky-900 space-y-2 list-decimal list-inside">
              <li className="font-bold text-brand-700">
                Subir / crear curso (actual)
              </li>
              <li>Análisis de contenido con IA</li>
              <li>Diseño pedagógico estructurado</li>
              <li>Generación de guion con escenas</li>
              <li>Generación de video con HeyGen</li>
              <li>Revisión QA y aprobación final</li>
            </ol>
          </div>

          <div className="card bg-violet-50 border-violet-200">
            <h3 className="font-semibold text-violet-900 mb-2">
              ¿No tienes PDF?
            </h3>
            <p className="text-sm text-violet-800">
              Puedes crear un curso solo con título y materia. El workflow
              funciona perfectamente sin documento adjunto en Modo Mock.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
