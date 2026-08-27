import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  AcademicCapIcon,
  CheckCircleIcon,
  BookOpenIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  ArrowPathIcon,
  ListBulletIcon,
} from '@heroicons/react/24/outline';
import ObjectivesList from '../components/ObjectivesList';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import { triggerPedagogical, getPedagogical, isNotFoundError } from '../services/courses';
import type { PedagogicalDesign } from '../types/pedagogical';

export default function Pedagogical() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentCourseId, setCurrentCourse, updateCourseMeta, getRouteForStep } = useCurrentCourse();
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [data, setData] = useState<PedagogicalDesign | null>(null);
  const [error, setError] = useState<string | null>(null);

  const courseId = id || currentCourseId || '';

  useEffect(() => {
    if (id && currentCourseId && id !== currentCourseId) {
      setCurrentCourse(id);
      return;
    }
    if (courseId && !id) {
      navigate(`/pedagogical/${courseId}`, { replace: true });
    }
  }, [courseId, id, currentCourseId, navigate, setCurrentCourse]);

  async function loadData(cid: string) {
    if (!cid) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await getPedagogical(cid);
      setData(result.pedagogical_design ?? null);
    } catch (err: any) {
      if (isNotFoundError(err)) {
        setData(null);
      } else {
        setError(err?.message || 'No se pudo cargar el diseño pedagógico');
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleRegenerate() {
    if (!courseId) return;
    setRegenerating(true);
    setError(null);
    try {
      const result = await triggerPedagogical(courseId);
      if (result.pedagogical_design) {
        setData(result.pedagogical_design);
      } else {
        await loadData(courseId);
      }
      updateCourseMeta({ progress: 40, status: 'PEDAGOGICAL_DESIGN' });
      setCurrentCourse(courseId);
    } catch (err: any) {
      setError(err?.message || 'Error al regenerar el diseño pedagógico');
    } finally {
      setRegenerating(false);
    }
  }

  useEffect(() => {
    loadData(courseId);
  }, [courseId]);

  const hasData = Boolean(data);
  const d = data!;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <AcademicCapIcon className="w-7 h-7 text-brand-600" />
            Diseño pedagógico
          </h1>
          <p className="text-slate-600 mt-1">
            Estructura educativa, objetivos, duración y estrategias para el curso.
          </p>
        </div>
        {hasData && (
          <button
            className="btn-pedagogical btn-lg"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            <ArrowPathIcon
              className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`}
            />
            {regenerating ? 'Regenerando...' : 'Regenerar diseño'}
          </button>
        )}
      </div>

      {error && (
        <div className="card bg-rose-50 border-rose-200 text-rose-800">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="card text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-slate-400 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Cargando diseño pedagógico...
          </h3>
          <p className="text-slate-500">
            Analizando la estructura educativa del curso.
          </p>
        </div>
      ) : !hasData ? (
        <div className="card text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
            <AcademicCapIcon className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Sin diseño pedagógico
          </h3>
          <p className="text-slate-500">
            Analiza un PDF y genera el diseño pedagógico para verlo aquí.
          </p>
          {courseId && (
            <button
              className="btn-pedagogical btn-xl mt-6 pulse-highlight"
              onClick={handleRegenerate}
              disabled={regenerating}
            >
              <SparklesIcon className="w-5 h-5" />
              {regenerating ? 'Generando diseño pedagógico...' : 'Generar diseño pedagógico con IA'}
            </button>
          )}
        </div>
      ) : (
        (() => {
          void d;
          return (
            <div className="space-y-6">
          <div className="card bg-gradient-to-br from-sky-50 to-white border-sky-200">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-lg bg-sky-100 flex items-center justify-center shrink-0">
                <AcademicCapIcon className="w-5 h-5 text-sky-700" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-slate-900 mb-2">
                  Objetivo general
                </h2>
                <p className="text-slate-700 leading-relaxed">
                  {d.general_objective}
                </p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircleIcon className="w-5 h-5 text-emerald-600" />
                <h3 className="font-semibold text-slate-900">
                  Objetivos específicos
                </h3>
              </div>
              {d.specific_objectives && d.specific_objectives.length > 0 ? (
                <ObjectivesList objectives={d.specific_objectives} />
              ) : (
                <p className="text-sm text-slate-500">No hay objetivos específicos.</p>
              )}
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <ListBulletIcon className="w-5 h-5 text-violet-600" />
                <h3 className="font-semibold text-slate-900">Prerrequisitos</h3>
              </div>
              {d.prerequisites && d.prerequisites.length > 0 ? (
                <ul className="space-y-2">
                  {d.prerequisites.map((p, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-700">
                      <span className="text-violet-600 font-bold shrink-0">•</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">Sin prerrequisitos.</p>
              )}
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <BookOpenIcon className="w-5 h-5 text-sky-600" />
              <h3 className="font-semibold text-slate-900">
                Estructura de la lección
              </h3>
            </div>
            {d.lesson_structure && d.lesson_structure.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...d.lesson_structure]
                  .sort((a, b) => (a.order || 0) - (b.order || 0))
                  .map((item, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-slate-200 bg-slate-50 p-4 hover:shadow-sm transition-shadow"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xs font-bold">
                            {item.order || i + 1}
                          </span>
                          <h4 className="font-semibold text-slate-900 text-sm">
                            {item.module}
                          </h4>
                        </div>
                        {item.duration_minutes && (
                          <span className="badge bg-slate-200 text-slate-700 shrink-0">
                            <ClockIcon className="w-3 h-3" />
                            {item.duration_minutes} min
                          </span>
                        )}
                      </div>
                      {item.purpose && (
                        <p className="text-xs text-slate-600 mb-2 italic">
                          {item.purpose}
                        </p>
                      )}
                      {item.topics && item.topics.length > 0 && (
                        <ul className="text-xs text-slate-700 space-y-1">
                          {item.topics.map((t, j) => (
                            <li key={j} className="flex gap-1">
                              <span className="text-slate-400">-</span>
                              <span>{t}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Sin estructura de lección definida.
              </p>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <LightBulbIcon className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-slate-900">Ejemplos prácticos</h3>
              </div>
              {d.examples && d.examples.length > 0 ? (
                <div className="space-y-4">
                  {d.examples.map((ex, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-amber-200 bg-amber-50 p-4"
                    >
                      <h4 className="font-semibold text-sm text-amber-900 mb-1">
                        {ex.title}
                      </h4>
                      <p className="text-sm text-amber-800 mb-2">
                        {ex.description}
                      </p>
                      {ex.explanation && (
                        <p className="text-xs text-amber-700 border-t border-amber-200 pt-2 mt-2">
                          <span className="font-semibold">Explicación: </span>
                          {ex.explanation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">Sin ejemplos disponibles.</p>
              )}
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <ExclamationTriangleIcon className="w-5 h-5 text-rose-600" />
                <h3 className="font-semibold text-slate-900">
                  Errores comunes
                </h3>
              </div>
              {d.common_mistakes && d.common_mistakes.length > 0 ? (
                <div className="space-y-3">
                  {d.common_mistakes.map((cm, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-rose-200 bg-rose-50 p-3"
                    >
                      <div className="flex items-start gap-2">
                        <span className="badge bg-rose-200 text-rose-800 text-[10px] shrink-0 mt-0.5">
                          Error
                        </span>
                        <p className="text-sm font-medium text-rose-900">
                          {cm.mistake}
                        </p>
                      </div>
                      {cm.context && (
                        <p className="text-xs text-rose-700 mt-1 italic">
                          Contexto: {cm.context}
                        </p>
                      )}
                      <div className="mt-2 pt-2 border-t border-rose-200">
                        <span className="badge bg-emerald-100 text-emerald-700 text-[10px]">
                          Corrección
                        </span>
                        <p className="text-sm text-emerald-900 mt-1">
                          {cm.correction}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  No se identificaron errores comunes.
                </p>
              )}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <SparklesIcon className="w-5 h-5 text-indigo-600" />
                <h3 className="font-semibold text-slate-900">
                  Estrategias de enseñanza
                </h3>
              </div>
              {d.teaching_strategies && d.teaching_strategies.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {d.teaching_strategies.map((s, i) => (
                    <span
                      key={i}
                      className="badge bg-indigo-100 text-indigo-700"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  Sin estrategias definidas.
                </p>
              )}
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <ClipboardDocumentListIcon className="w-5 h-5 text-teal-600" />
                <h3 className="font-semibold text-slate-900">
                  Métodos de evaluación
                </h3>
              </div>
              {d.assessment_methods && d.assessment_methods.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {d.assessment_methods.map((m, i) => (
                    <span
                      key={i}
                      className="badge bg-teal-100 text-teal-700"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">
                  Sin métodos de evaluación.
                </p>
              )}
            </div>
          </div>

          <div className="card bg-slate-50">
            <div className="grid md:grid-cols-3 gap-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <ClockIcon className="w-5 h-5 text-slate-600" />
                  <h3 className="font-semibold text-slate-900">
                    Duración estimada
                  </h3>
                </div>
                <p className="text-2xl font-bold text-brand-700">
                  {d.estimated_duration_minutes || 0}{' '}
                  <span className="text-sm font-normal text-slate-500">min</span>
                </p>
              </div>
              <div className="md:col-span-2">
                <h3 className="font-semibold text-slate-900 mb-2">
                  Actividad sugerida
                </h3>
                {d.activity_suggested ? (
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {d.activity_suggested}
                  </p>
                ) : (
                  <p className="text-sm text-slate-500 italic">
                    No hay actividad sugerida.
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-slate-900 mb-2">
              Resumen del enfoque pedagógico
            </h3>
            <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
              {d.summary}
            </p>
          </div>

          <div className="pt-2">
            <NextStepButton
              overrideLabel="Continuar → Generar Guion con Escenas"
              overrideRoute={getRouteForStep('script')}
              description="Convierte el diseño pedagógico en escenas ordenadas, narración escrita e instrucciones visuales por lección para el video final"
              size="xl" block highlight
              disabled={!hasData}
            />
          </div>
        </div>
          );
        })()
      )}
    </div>
  );
}
