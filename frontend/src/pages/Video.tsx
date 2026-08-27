import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowPathIcon,
  PlayIcon,
  VideoCameraIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import VideoPlayer from '../components/VideoPlayer';
import ProgressBar from '../components/ProgressBar';
import StatusBadge from '../components/StatusBadge';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import {
  triggerGenerateVideo,
  getCourseStatus,
  getVideo,
  pollVideoStatus,
  isNotFoundError,
} from '../services/courses';
import type { CourseStatus, VideoInfo } from '../services/courses';

export default function Video() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentCourseId, setCurrentCourse, updateCourseMeta, getRouteForStep } = useCurrentCourse();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<CourseStatus | null>(null);
  const [latestVideo, setLatestVideo] = useState<VideoInfo | null>(null);
  const pollingRef = useRef<number | null>(null);

  const courseId = id || currentCourseId || '';
  const status = latestVideo?.status || statusData?.status || '';
  const progress = statusData?.progress ?? 0;
  const videoUrl =
    latestVideo?.url || statusData?.video?.url || (statusData as any)?.video?.video_url || '';
  const thumbnail =
    latestVideo?.thumbnail_url ||
    statusData?.video?.thumbnail_url ||
    (statusData as any)?.video?.thumbnail_url ||
    '';
  const duration = latestVideo?.duration ?? statusData?.video?.duration ?? 0;
  const qa = statusData?.qa;

  useEffect(() => {
    if (id && currentCourseId && id !== currentCourseId) {
      setCurrentCourse(id);
      return;
    }
    if (courseId && !id) {
      navigate(`/video/${courseId}`, { replace: true });
    }
  }, [courseId, id, currentCourseId, navigate, setCurrentCourse]);

  async function loadStatus(cid: string) {
    if (!cid) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [s, v] = await Promise.all([
        getCourseStatus(cid),
        getVideo(cid).catch((e) => (isNotFoundError(e) ? null : Promise.reject(e))),
      ]);
      const merged = { ...s };
      if (v) {
        setLatestVideo(v);
        if (v.url) {
          merged.video = {
            ...(merged.video ?? ({} as any)),
            url: v.url,
          };
        }
        if (v.status && v.status !== 'SUBMITTED' && v.status !== 'PROCESSING') {
          merged.status = v.status;
        }
      }
      if (!merged.video && (s as any).video) {
        const rawVid = (s as any).video;
        const sUrl = rawVid.video_url || rawVid.url;
        const sThumb = rawVid.thumbnail_url;
        merged.video = {
          url: sUrl || '',
          thumbnail_url: sThumb,
          duration: rawVid.duration || 0,
        };
        if (!latestVideo && rawVid.id) {
          setLatestVideo({
            id: rawVid.id,
            url: sUrl,
            thumbnail_url: sThumb,
            duration: rawVid.duration,
            status: rawVid.status,
            provider: rawVid.provider,
            provider_video_id: rawVid.provider_video_id,
            course_id: cid,
          });
        }
      }
      setStatusData(merged);
      if (merged?.status) {
        updateCourseMeta({ progress: merged.progress ?? 0, status: merged.status });
      }
    } catch (err: any) {
      if (isNotFoundError(err)) {
        setStatusData(null);
      } else {
        setError(err?.message || 'No se pudo cargar el estado del video');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    function isStillProcessing() {
      const s = (latestVideo?.status || statusData?.status || '').toUpperCase();
      const hasUrl = Boolean(videoUrl && videoUrl.length > 0);
      if (hasUrl) return false;
      return s === 'SUBMITTED' || s === 'PROCESSING' || s === 'VIDEO_GENERATING' || s === 'VIDEO_PROCESSING';
    }

    async function tickPoll() {
      try {
        const vidInfo = latestVideo;
        if (vidInfo && vidInfo.id && isStillProcessing()) {
          const refreshed = await pollVideoStatus(vidInfo.id);
          if (refreshed) {
            setLatestVideo((prev) => prev ? { ...prev, ...refreshed } : refreshed);
            if (refreshed.url && !videoUrl) {
              setStatusData((s) => s ? {
                ...s,
                status: refreshed.status || s.status,
                video: {
                  ...(s.video ?? ({} as any)),
                  url: refreshed.url,
                  thumbnail_url: refreshed.thumbnail_url,
                  duration: refreshed.duration ?? s.video?.duration ?? 0,
                },
              } : s);
            }
          }
        }
      } catch (e: any) {
        console.warn('[video-poll] tick failed', e?.message);
      }
    }

    if (courseId) {
      pollingRef.current = window.setInterval(tickPoll, 8000);
      return () => {
        if (pollingRef.current !== null) {
          window.clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      };
    }
  }, [courseId, latestVideo, statusData, videoUrl]);

  async function handleGenerate() {
    if (!courseId) return;
    setGenerating(true);
    setError(null);
    try {
      await triggerGenerateVideo(courseId);
      await loadStatus(courseId);
      setCurrentCourse(courseId);
    } catch (err: any) {
      setError(err?.message || 'Error al generar el video');
    } finally {
      setGenerating(false);
    }
  }

  useEffect(() => {
    loadStatus(courseId);
  }, [courseId]);

  const hasVideo =
    status === 'COMPLETED' ||
    status === 'VIDEO_READY' ||
    Boolean(videoUrl && videoUrl.length > 0);
  const canContinueQA = Boolean(hasVideo);

  function statusMessage(s: string) {
    switch (s) {
      case 'VIDEO_GENERATING':
        return 'Enviando solicitud al proveedor de video...';
      case 'VIDEO_PROCESSING':
        return 'Renderizando video en el proveedor...';
      case 'SCRIPT_GENERATED':
      case 'SCRIPT_VALIDATED':
        return 'Esperando aprobación del guion.';
      case 'PEDAGOGICAL_DESIGN':
        return 'Diseño pedagógico completado, esperando guion.';
      case 'ANALYZING':
      case 'EXTRACTING':
      case 'UPLOADED':
      case 'CREATED':
        return 'El video aún no ha sido generado. Completa las etapas previas.';
      case 'FAILED':
        return 'Ocurrió un error en el proceso.';
      default:
        return 'Esperando procesamiento.';
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <VideoCameraIcon className="w-7 h-7 text-rose-600" />
            Video del curso
          </h1>
          <p className="text-slate-600 mt-1">
            Visualiza el estado y reproduce el video final generado.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {status && <StatusBadge status={status} />}
          {!hasVideo && courseId && (
            <button
              className="btn-video btn-lg pulse-highlight"
              onClick={handleGenerate}
              disabled={generating}
            >
              <CloudArrowUpIcon
                className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`}
              />
              {generating ? 'Generando video...' : 'Generar video final'}
            </button>
          )}
          <button
            className="btn-secondary"
            onClick={() => loadStatus(courseId)}
            disabled={loading}
          >
            <ArrowPathIcon
              className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
            />
            Actualizar estado
          </button>
        </div>
      </div>

      {error && (
        <div className="card bg-rose-50 border-rose-200 text-rose-800">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          {loading ? (
            <div className="card text-center py-16 aspect-video flex items-center justify-center">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-slate-400 animate-spin"
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
            </div>
          ) : hasVideo ? (
            <div className="overflow-hidden rounded-2xl shadow-2xl border border-slate-200">
              <VideoPlayer url={videoUrl} thumbnail={thumbnail} />
            </div>
          ) : (
            <div className="aspect-video rounded-xl bg-slate-900 flex items-center justify-center text-white">
              <div className="text-center p-8 max-w-md">
                {status !== 'COMPLETED' && status !== 'VIDEO_READY' ? (
                  <ProgressBar progress={progress} />
                ) : null}
                <div className="w-16 h-16 mx-auto mt-6 mb-4 rounded-full bg-white/10 flex items-center justify-center">
                  <PlayIcon className="w-8 h-8 text-white/60" />
                </div>
                <p className="mt-4 text-sm text-slate-400">
                  {statusMessage(status)}
                </p>
                {!courseId && (
                  <p className="mt-2 text-xs text-slate-500">
                    Selecciona un curso para ver su video.
                  </p>
                )}
                {courseId && !hasVideo && !generating && (
                  <button
                    className="btn-video btn-xl mt-6 mx-auto pulse-highlight"
                    onClick={handleGenerate}
                  >
                    <CloudArrowUpIcon className="w-5 h-5" />
                    Generar video ahora
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-slate-900 mb-4">Detalles</h3>
            <dl className="text-sm space-y-3">
              <div className="flex justify-between">
                <dt className="text-slate-500">Progreso</dt>
                <dd className="font-medium">{progress}%</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Duración</dt>
                <dd className="font-medium">
                  {duration
                    ? `${Math.floor(duration / 60)}:${String(duration % 60).padStart(2, '0')}`
                    : '—'}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Provider</dt>
                <dd className="font-medium">HeyGen</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Modo</dt>
                <dd>
                  {(() => {
                    const p = (statusData as any)?.video?.provider || '';
                    const isMock = p === 'mock' || !p;
                    return (
                      <span
                        className={`badge ${
                          isMock
                            ? 'bg-violet-100 text-violet-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {isMock ? 'Mock' : `API ${String(p).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}`}
                      </span>
                    );
                  })()}
                </dd>
              </div>
            </dl>
          </div>

          {qa && (
            <div className="card">
              <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                Control de calidad
              </h3>
              <dl className="text-sm space-y-2">
                <div className="flex justify-between items-center">
                  <dt className="text-slate-500">Estado</dt>
                  <dd>
                    <span
                      className={`badge ${
                        qa.status === 'approved'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-rose-100 text-rose-700'
                      }`}
                    >
                      {qa.status === 'approved' ? 'Aprobado' : 'Rechazado'}
                    </span>
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Puntuación</dt>
                  <dd
                    className={`font-bold text-lg ${
                      qa.score >= 80
                        ? 'text-emerald-600'
                        : qa.score >= 50
                        ? 'text-amber-600'
                        : 'text-rose-600'
                    }`}
                  >
                    {qa.score}/100
                  </dd>
                </div>
              </dl>
            </div>
          )}

          <div className="card bg-brand-50 border-brand-200">
            <h3 className="font-semibold text-brand-900 mb-2">Pasos del flujo</h3>
            <ol className="text-xs text-brand-800 space-y-2 list-decimal list-inside">
              <li className={progress >= 25 ? 'text-emerald-700 font-medium' : ''}>
                Extracción y análisis del PDF
              </li>
              <li className={progress >= 40 ? 'text-emerald-700 font-medium' : ''}>
                Diseño pedagógico
              </li>
              <li className={progress >= 60 ? 'text-emerald-700 font-medium' : ''}>
                Generación de guion
              </li>
              <li className={progress >= 70 ? 'text-emerald-700 font-medium' : ''}>
                Aprobación de guion
              </li>
              <li className={progress >= 90 ? 'text-emerald-700 font-medium' : ''}>
                Generación de video
              </li>
              <li className={progress >= 100 ? 'text-emerald-700 font-medium' : ''}>
                Revisión QA y finalización
              </li>
            </ol>
          </div>
        </div>
      </div>

      {hasVideo && (
        <div className="card-step border-emerald-300">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
              <CheckCircleIcon className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-emerald-900">
                ¡Video generado exitosamente!
              </h3>
              <p className="text-sm text-emerald-800 mt-1">
                El video final está listo para reproducir. Continúa a la etapa
                de Revisión QA para validar la calidad general del contenido.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="pt-2">
        <NextStepButton
          overrideLabel={
            canContinueQA
              ? 'Continuar → Revisión QA de Calidad'
              : hasVideo
              ? 'Revisión QA disponible →'
              : 'Genera el video para continuar →'
          }
          overrideRoute={getRouteForStep('qa')}
          description={
            canContinueQA
              ? 'Ejecuta la revisión automática de calidad sobre el guion, video y contenido pedagógico con puntuación numérica'
              : 'Primero genera el video final (botón rosa arriba a la derecha) para habilitar la etapa QA'
          }
          size="xl" block={true} highlight={Boolean(canContinueQA)}
          disabled={Boolean(!canContinueQA)}
        />
      </div>
    </div>
  );
}
