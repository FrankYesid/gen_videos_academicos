import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  LightBulbIcon,
  DocumentTextIcon,
  InformationCircleIcon,
  HomeIcon,
  PlayCircleIcon,
} from '@heroicons/react/24/outline';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import { triggerQAReview, getQA, isNotFoundError } from '../services/courses';
import type { QAResult, QAIssue, QASeverity } from '../types/qa';

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600';
  if (score >= 50) return 'text-amber-600';
  return 'text-rose-600';
}

function getScoreStroke(score: number): string {
  if (score >= 80) return '#059669';
  if (score >= 50) return '#d97706';
  return '#e11d48';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'from-emerald-50 to-white';
  if (score >= 50) return 'from-amber-50 to-white';
  return 'from-rose-50 to-white';
}

function getSeverityBadge(severity: QASeverity) {
  switch (severity) {
    case 'high':
      return 'bg-rose-100 text-rose-700 border-rose-200';
    case 'medium':
      return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'low':
    default:
      return 'bg-sky-100 text-sky-700 border-sky-200';
  }
}

function getSeverityLabel(severity: QASeverity) {
  switch (severity) {
    case 'high':
      return 'Alto';
    case 'medium':
      return 'Medio';
    case 'low':
    default:
      return 'Bajo';
  }
}

function ScoreCircle({ score }: { score: number }) {
  const size = 160;
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  const strokeColor = getScoreStroke(score);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-extrabold ${getScoreColor(score)}`}>
          {score}
        </span>
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          / 100
        </span>
      </div>
    </div>
  );
}

export default function QA() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentCourseId, setCurrentCourse, updateCourseMeta } = useCurrentCourse();
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [data, setData] = useState<QAResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const courseId = id || currentCourseId || '';

  useEffect(() => {
    if (id && currentCourseId && id !== currentCourseId) {
      setCurrentCourse(id);
      return;
    }
    if (courseId && !id) {
      navigate(`/qa/${courseId}`, { replace: true });
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
      const result = await getQA(cid);
      setData(result.qa ?? null);
    } catch (err: any) {
      if (isNotFoundError(err)) {
        setData(null);
      } else {
        setError(err?.message || 'No se pudo cargar la revisión de calidad');
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
      const result = await triggerQAReview(courseId);
      if (result.qa) {
        setData(result.qa);
      } else {
        await loadData(courseId);
      }
      updateCourseMeta({ progress: 100, status: 'COMPLETED' });
      setCurrentCourse(courseId);
    } catch (err: any) {
      setError(err?.message || 'Error al regenerar la revisión de calidad');
    } finally {
      setRegenerating(false);
    }
  }

  useEffect(() => {
    loadData(courseId);
  }, [courseId]);

  const hasData = Boolean(data);
  const d = data!;
  const isApproved = Boolean(hasData && d.status === 'approved');

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheckIcon className="w-7 h-7 text-amber-600" />
            Revisión de calidad (QA)
          </h1>
          <p className="text-slate-600 mt-1">
            Verificación automática del guion, calidad pedagógica y contenido.
          </p>
        </div>
        {hasData && (
          <button
            className="btn-qa btn-lg"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            <ArrowPathIcon
              className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`}
            />
            {regenerating ? 'Regenerando QA...' : 'Regenerar QA'}
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
            Cargando revisión de calidad...
          </h3>
          <p className="text-slate-500">
            Analizando el guion y contenido del curso.
          </p>
        </div>
      ) : !hasData ? (
        <div className="card text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
            <ShieldCheckIcon className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Sin revisión de calidad
          </h3>
          <p className="text-slate-500">
            Genera el guion y/o video para ejecutar la revisión QA.
          </p>
          {courseId && (
            <button
              className="btn-qa btn-xl mt-6 pulse-highlight"
              onClick={handleRegenerate}
              disabled={regenerating}
            >
              <ShieldCheckIcon className="w-5 h-5" />
              {regenerating ? 'Ejecutando QA...' : 'Ejecutar revisión QA'}
            </button>
          )}
        </div>
      ) : (() => {
        void d;
        return (
          <div className="space-y-6">
            <div
              className={`card bg-gradient-to-br ${getScoreBg(
                d.score ?? 0,
              )}`}
            >
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="shrink-0">
                  <ScoreCircle score={d.score ?? 0} />
                </div>
                <div className="flex-1 text-center md:text-left">
                  <div className="flex flex-col sm:flex-row items-center gap-3 mb-4 justify-center md:justify-start">
                    <h2 className="text-xl font-bold text-slate-900">
                      Estado general
                    </h2>
                    <span
                      className={`badge border px-3 py-1 ${
                        isApproved
                          ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                          : 'bg-rose-100 text-rose-700 border-rose-200'
                      }`}
                    >
                      {isApproved ? (
                        <CheckCircleIcon className="w-4 h-4" />
                      ) : (
                        <XCircleIcon className="w-4 h-4" />
                      )}
                      {isApproved ? 'Aprobado' : 'Rechazado'}
                    </span>
                  </div>
                  {d.summary && (
                    <p className="text-slate-700 leading-relaxed max-w-2xl">
                      {d.summary}
                    </p>
                  )}
                  <div className="mt-4 grid grid-cols-3 gap-4 max-w-md mx-auto md:mx-0">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-slate-900">
                        {(d.issues || []).filter((i) => i.severity === 'high').length}
                      </p>
                      <p className="text-xs text-rose-600 font-medium">
                        Graves
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-slate-900">
                        {(d.issues || []).filter((i) => i.severity === 'medium').length}
                      </p>
                      <p className="text-xs text-amber-600 font-medium">
                        Medios
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-slate-900">
                        {(d.issues || []).filter((i) => i.severity === 'low').length}
                      </p>
                      <p className="text-xs text-sky-600 font-medium">Leves</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <ExclamationTriangleIcon className="w-5 h-5 text-rose-600" />
                <h3 className="font-semibold text-slate-900">
                  Problemas detectados
                </h3>
                <span className="badge bg-slate-100 text-slate-700">
                  {(d.issues || []).length} total
                </span>
              </div>
              {(d.issues || []).length === 0 ? (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 text-center">
                  <CheckCircleIcon className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
                  <p className="font-medium text-emerald-800">
                    ¡Sin problemas detectados!
                  </p>
                  <p className="text-sm text-emerald-700 mt-1">
                    El contenido cumple con todos los criterios de calidad.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {[...(d.issues || [])]
                    .sort((a, b) => {
                      const order = { high: 0, medium: 1, low: 2 } as Record<
                        QASeverity,
                        number
                      >;
                      return order[a.severity] - order[b.severity];
                    })
                    .map((issue: QAIssue, i: number) => (
                      <div
                        key={i}
                        className="rounded-lg border border-slate-200 bg-white p-4 hover:shadow-sm transition-shadow"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`badge border ${getSeverityBadge(
                                issue.severity,
                              )}`}
                            >
                              {getSeverityLabel(issue.severity)}
                            </span>
                            <span className="badge bg-slate-100 text-slate-700">
                              <DocumentTextIcon className="w-3 h-3" />
                              {issue.category}
                            </span>
                            {issue.scene_id !== undefined &&
                              issue.scene_id !== null && (
                                <span className="badge bg-indigo-100 text-indigo-700">
                                  Escena #{issue.scene_id}
                                </span>
                              )}
                          </div>
                        </div>
                        <p className="text-sm text-slate-800 mb-2 font-medium">
                          {issue.description}
                        </p>
                        {issue.suggestion && (
                          <div className="rounded-md bg-slate-50 border border-slate-200 p-3 mt-2">
                            <div className="flex items-start gap-2">
                              <LightBulbIcon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                              <div>
                                <p className="text-xs font-semibold text-amber-700 mb-0.5">
                                  Sugerencia
                                </p>
                                <p className="text-sm text-slate-700">
                                  {issue.suggestion}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>

            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <LightBulbIcon className="w-5 h-5 text-amber-600" />
                <h3 className="font-semibold text-slate-900">Recomendaciones</h3>
              </div>
              {(d.recommendations || []).length === 0 ? (
                <div className="flex items-start gap-2 text-slate-600">
                  <InformationCircleIcon className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                  <p className="text-sm italic">
                    No hay recomendaciones adicionales.
                  </p>
                </div>
              ) : (
                <ol className="space-y-3">
                  {(d.recommendations || []).map((rec, i) => (
                    <li key={i} className="flex gap-3">
                      <div className="shrink-0 w-7 h-7 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-sm">
                        {i + 1}
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed pt-1">
                        {rec}
                      </p>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            {isApproved && (
              <div className="card-step border-emerald-300">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <CheckCircleIcon className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-emerald-900 text-lg">
                      🎉 ¡Flujo de trabajo completado!
                    </h3>
                    <p className="text-sm text-emerald-800 mt-1">
                      El curso ha superado la revisión QA con una puntuación de{' '}
                      <span className="font-bold">{d.score}/100</span>. Ya
                      puedes volver al Dashboard para ver el resumen, reproducir
                      el video final o crear un nuevo curso.
                    </p>
                    <div className="flex flex-wrap gap-3 mt-4">
                      <Link
                        to="/"
                        className="btn-continue btn-lg"
                      >
                        <HomeIcon className="w-4 h-4" />
                        Volver al Dashboard
                      </Link>
                      {courseId && (
                        <Link
                          to={`/video/${courseId}`}
                          className="btn-video btn-lg"
                        >
                          <PlayCircleIcon className="w-4 h-4" />
                          Reproducir video final
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })()}

      <div className="pt-2">
        <NextStepButton
          overrideLabel={
            isApproved
              ? '✅ Volver al Dashboard - Curso Completado'
              : hasData
              ? 'Regenera QA hasta aprobar →'
              : 'Ejecuta QA para finalizar →'
          }
          description={
            isApproved
              ? 'Regresa al panel principal para visualizar todos tus cursos, su progreso y el video final del curso aprobado'
              : 'Ejecuta la revisión automática y asegúrate de que la puntuación sea ≥80 para aprobar y finalizar el flujo'
          }
          size="xl" block highlight={isApproved}
          disabled={!isApproved && !hasData}
          overrideRoute={isApproved ? '/' : undefined}
        />
      </div>
    </div>
  );
}
