import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowPathIcon,
  CheckCircleIcon,
  PlayCircleIcon,
  DocumentTextIcon,
  UsersIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import ScriptViewer from '../components/ScriptViewer';
import StatusBadge from '../components/StatusBadge';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import {
  triggerScript,
  approveScript,
  getScript,
  isNotFoundError,
} from '../services/courses';
import type { Script } from '../types/script';

export default function ScriptPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentCourseId, setCurrentCourse, updateCourseMeta, getRouteForStep } = useCurrentCourse();
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [data, setData] = useState<Script | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');

  const courseId = id || currentCourseId || '';

  useEffect(() => {
    if (id && currentCourseId && id !== currentCourseId) {
      setCurrentCourse(id);
      return;
    }
    if (courseId && !id) {
      navigate(`/script/${courseId}`, { replace: true });
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
      const result = await getScript(cid);
      setData(result.script ?? null);
    } catch (err: any) {
      if (isNotFoundError(err)) {
        setData(null);
      } else {
        setError(err?.message || 'No se pudo cargar el guion');
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
      const result = await triggerScript(courseId);
      if (result.script) {
        setData(result.script);
      } else {
        await loadData(courseId);
      }
      updateCourseMeta({ progress: 60, status: 'SCRIPT_GENERATED' });
      setCurrentCourse(courseId);
    } catch (err: any) {
      setError(err?.message || 'Error al regenerar el guion');
    } finally {
      setRegenerating(false);
    }
  }

  async function handleApprove() {
    if (!courseId) return;
    setApproving(true);
    setError(null);
    try {
      const result = await approveScript(courseId);
      if ((result as any)?.status) {
        setStatus((result as any).status);
      }
      setStatus('SCRIPT_VALIDATED');
      updateCourseMeta({ progress: 70, status: 'SCRIPT_VALIDATED' });
      setCurrentCourse(courseId);
    } catch (err: any) {
      setError(err?.message || 'Error al aprobar el guion');
    } finally {
      setApproving(false);
    }
  }

  useEffect(() => {
    loadData(courseId);
  }, [courseId]);

  const hasData = Boolean(data);
  const d = data!;
  const isApproved = status === 'SCRIPT_VALIDATED';
  const canContinue = Boolean(hasData && isApproved);

  function formatDuration(sec: number) {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <DocumentTextIcon className="w-7 h-7 text-emerald-600" />
            Guion del curso
          </h1>
          <p className="text-slate-600 mt-1">
            Revisa las escenas generadas. Aprueba para generar el video o
            regenera el guion.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {status && <StatusBadge status={status} />}
          {hasData && (
            <>
              <button
                className="btn-secondary"
                onClick={handleRegenerate}
                disabled={regenerating}
              >
                <ArrowPathIcon
                  className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`}
                />
                {regenerating ? 'Regenerando...' : 'Regenerar guion'}
              </button>
              <button
                className="btn-script btn-lg"
                onClick={handleApprove}
                disabled={approving || isApproved}
              >
                <CheckCircleIcon className="w-4 h-4" />
                {approving
                  ? 'Aprobando...'
                  : isApproved
                  ? '✓ Aprobado'
                  : 'Aprobar guion'}
              </button>
            </>
          )}
        </div>
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
            Cargando guion...
          </h3>
          <p className="text-slate-500">
            Obteniendo las escenas y estructura del guion.
          </p>
        </div>
      ) : !hasData ? (
        <div className="card text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
            <PlayCircleIcon className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Sin guiones generados
          </h3>
          <p className="text-slate-500">
            Sube y analiza un PDF para que la IA genere automáticamente el guion
            del curso.
          </p>
          {courseId && (
            <button
              className="btn-script btn-xl mt-6 pulse-highlight"
              onClick={handleRegenerate}
              disabled={regenerating}
            >
              <SparklesIcon className="w-5 h-5" />
              {regenerating ? 'Generando guion...' : 'Generar guion con IA'}
            </button>
          )}
        </div>
      ) : (() => {
        void d;
        return (
          <>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="card">
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
                  Duración total
                </p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {formatDuration(d.total_duration_seconds || 0)}
                </p>
              </div>
              <div className="card">
                <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
                  Escenas
                </p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {(d.scenes || []).length}
                </p>
              </div>
              <div className="card">
                <div className="flex items-center gap-1.5 mb-1">
                  <UsersIcon className="w-3.5 h-3.5 text-slate-400" />
                  <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
                    Audiencia
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-900 truncate">
                  {d.target_audience || '—'}
                </p>
              </div>
              <div className="card">
                <div className="flex items-center gap-1.5 mb-1">
                  <SparklesIcon className="w-3.5 h-3.5 text-slate-400" />
                  <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">
                    Tono
                  </p>
                </div>
                <p className="text-sm font-semibold text-slate-900 capitalize">
                  {d.tone || 'educational'}
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="card bg-gradient-to-br from-violet-50 to-white">
                <h3 className="font-semibold text-slate-900 mb-2">
                  Introducción
                </h3>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {d.introduction || 'Sin introducción.'}
                </p>
              </div>
              <div className="card bg-gradient-to-br from-emerald-50 to-white">
                <h3 className="font-semibold text-slate-900 mb-2">Conclusión</h3>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {d.conclusion || 'Sin conclusión.'}
                </p>
              </div>
            </div>

            {d.notes && (
              <div className="card bg-amber-50 border-amber-200">
                <h3 className="font-semibold text-amber-900 mb-2">
                  Notas de producción
                </h3>
                <p className="text-sm text-amber-800 leading-relaxed whitespace-pre-wrap">
                  {d.notes}
                </p>
              </div>
            )}

            <ScriptViewer script={d as any} />

            {isApproved && (
              <div className="card-step border-emerald-300">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                    <CheckCircleIcon className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-emerald-900">
                      ¡Guion aprobado correctamente!
                    </h3>
                    <p className="text-sm text-emerald-800 mt-1">
                      El guion fue validado. Ahora puedes avanzar a la generación
                      del video final con el proveedor HeyGen.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="pt-2">
              <NextStepButton
                overrideLabel={
                  canContinue
                    ? 'Continuar → Generar Video Final'
                    : hasData
                    ? 'Aprobar el guion para continuar →'
                    : 'Genera un guion para continuar →'
                }
                overrideRoute={getRouteForStep('video')}
                description={
                  canContinue
                    ? 'Renderiza el curso en video con avatar, narración profesional y escenas animadas vía HeyGen'
                    : 'Primero genera y luego APRUEBA el guion (botón verde arriba a la derecha) para habilitar la generación del video'
                }
                size="xl" block highlight={canContinue}
                disabled={!canContinue}
              />
            </div>
          </>
        );
      })()}
    </div>
  );
}
