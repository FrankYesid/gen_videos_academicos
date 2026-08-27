import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  BeakerIcon,
  SparklesIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import AnalysisViewer from '../components/AnalysisViewer';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import {
  getAnalysis as getAnalysisApi,
  triggerAnalysis,
  isNotFoundError,
} from '../services/courses';
import type { Analysis } from '../types/analysis';

export default function Analysis() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentCourseId,
    setCurrentCourse,
    updateCourseMeta,
    getRouteForStep,
  } = useCurrentCourse();
  const courseId = id || currentCourseId || '';

  useEffect(() => {
    if (id && currentCourseId && id !== currentCourseId) {
      setCurrentCourse(id);
      return;
    }
    if (courseId && !id) {
      navigate(`/analysis/${courseId}`, { replace: true });
    }
  }, [courseId, id, currentCourseId, navigate, setCurrentCourse]);

  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [data, setData] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load(cid: string) {
    if (!cid) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await getAnalysisApi(cid);
      const analysis = res?.analysis;
      setData(analysis ?? null);
      if (analysis) {
        updateCourseMeta({ progress: 25, status: 'ANALYZING' });
      }
    } catch (err: any) {
      if (isNotFoundError(err)) {
        setData(null);
      } else {
        setError(err?.response?.data?.detail || err?.message || 'No se pudo cargar el análisis');
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleExecute() {
    if (!courseId) return;
    setExecuting(true);
    setError(null);
    try {
      const result = await triggerAnalysis(courseId);
      setCurrentCourse(courseId);
      if (result?.analysis) {
        setData(result.analysis as Analysis);
      } else {
        await load(courseId);
      }
      updateCourseMeta({ progress: 25, status: 'PEDAGOGICAL_DESIGN' });
    } catch (err: any) {
      setError(err?.message || 'Error al ejecutar el análisis');
    } finally {
      setExecuting(false);
    }
  }

  useEffect(() => {
    if (courseId && !id) navigate(`/analysis/${courseId}`, { replace: true });
    load(courseId);
  }, [courseId]);

  const hasData = !!data;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BeakerIcon className="w-7 h-7 text-violet-600" />
            Paso 2 · Análisis del contenido
          </h1>
          <p className="text-slate-600 mt-1">
            Identifica temas clave, conceptos, prerrequisitos y objetivos del curso.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="badge bg-violet-100 text-violet-700">
            Paso 2 de 6 · ~20%
          </span>
          {hasData && (
            <button
              type="button"
              onClick={handleExecute}
              disabled={executing}
              className="btn-secondary"
              title="Ejecuta de nuevo el análisis para refrescar conceptos y temas (consulta nuevamente al proveedor IA / Mock)"
            >
              <SparklesIcon
                className={`w-4 h-4 ${executing ? 'animate-spin' : ''}`}
              />
              {executing ? 'Regenerando...' : 'Regenerar análisis'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="card bg-rose-50 border-rose-200 text-rose-800">
          <p className="font-semibold">Error al cargar análisis</p>
          <p className="text-sm mt-1">{error}</p>
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
              <circle cx="12" cy="12" r="10" strokeWidth="4" className="opacity-25" stroke="currentColor" />
              <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900 mb-1">Cargando análisis</h3>
          <p className="text-slate-500">Procesando el contenido del curso.</p>
        </div>
      ) : !courseId ? (
        <div className="card text-center py-16">
          <BeakerIcon className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            Aún no has creado un curso
          </h3>
          <p className="text-slate-500 mb-4">
            Primero crea un curso en la sección Subir PDF para analizar su contenido.
          </p>
          <NextStepButton overrideRoute="/upload" overrideLabel="Crear curso primero" />
        </div>
      ) : !hasData ? (
        <div className="card-step border-violet-300 bg-gradient-to-br from-violet-50 to-white">
          <div className="text-center py-10">
            <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-violet-100 flex items-center justify-center">
              <BeakerIcon className="w-10 h-10 text-violet-600" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">
              Ejecuta el análisis IA por primera vez
            </h3>
            <p className="text-slate-600 mb-6 max-w-2xl mx-auto">
              Detecta automáticamente <strong>temas clave, conceptos, prerrequisitos, keywords y objetivos</strong>.
              En modo Mock retorna contenido determinista (no gasta APIs).
            </p>
            <button
              type="button"
              onClick={handleExecute}
              disabled={executing}
              className="btn-analysis btn-xl btn-block pulse-highlight"
              title="Ejecuta el Analyzer Agent: invoca OpenAI (o MockOpenAI si no hay key) con prompt versionado prompts/analyzer.txt y guarda el resultado JSONB en la columna analysis_data de courses."
            >
              {executing ? (
                <SparklesIcon className="w-6 h-6 animate-spin" />
              ) : (
                <BeakerIcon className="w-6 h-6" />
              )}
              <div className="flex flex-col items-start gap-0.5 text-left">
                <span>
                  {executing ? 'Analizando el contenido...' : '🔬 Realizar análisis IA'}
                </span>
                <span className="text-xs font-normal text-white/85 pl-9">
                  Extrae temas, conceptos, palabras clave, objetivos y resumen del curso
                </span>
              </div>
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="card-step border-emerald-300 bg-gradient-to-br from-emerald-50/60 to-white">
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                <CheckCircleIcon className="w-7 h-7 text-emerald-600" />
              </div>
              <div className="flex-1 text-center sm:text-left">
                <h2 className="text-lg font-bold text-emerald-900">
                  ¡Análisis completado!
                </h2>
                <p className="text-emerald-800 text-sm">
                  Datos extraídos correctamente. Revisa el contenido y continúa al diseño pedagógico.
                </p>
              </div>
            </div>
          </div>

          <AnalysisViewer analysis={data as any} />

          <div className="pt-2">
            <NextStepButton
              overrideLabel="Continuar → Diseño Pedagógico"
              overrideRoute={getRouteForStep('pedagogical')}
              description="Estructura lecciones, ejemplos prácticos, errores comunes y estrategias didácticas para el curso"
              size="xl"
              block
              highlight
            />
          </div>
        </>
      )}
    </div>
  );
}
