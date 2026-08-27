import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRightIcon,
  CloudArrowUpIcon,
  BeakerIcon,
  PlayIcon,
  AcademicCapIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import CourseCard, { CourseCardData } from '../components/CourseCard';
import NextStepButton from '../components/NextStepButton';
import { useCurrentCourse } from '../contexts/CurrentCourseContext';
import { listCourses } from '../services/courses';
import type { CourseListItem } from '../types/course';

export default function Dashboard() {
  const {
    currentCourseId,
    getNextStep,
    currentCourseMeta,
    setCurrentCourse,
    clearCurrentCourse,
  } = useCurrentCourse();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [courses, setCourses] = useState<CourseCardData[]>([]);

  async function loadCourses() {
    setLoading(true);
    setError(null);
    try {
      const res = await listCourses();
      const items = (res?.items ?? []) as CourseListItem[];
      const mapped: CourseCardData[] = items.map((c) => ({
        id: c.id,
        title: c.title || 'Curso sin título',
        subject: c.subject || 'General',
        status: c.status,
        duration: c.progress ?? 0,
        createdAt: c.created_at,
      }));
      setCourses(mapped);

      if (!currentCourseId && mapped.length > 0) {
        const inProgress = mapped.find(
          (c) => c.status !== 'COMPLETED' && c.status !== 'FAILED',
        );
        const target = inProgress ?? mapped[0];
        setCurrentCourse(target.id, {
          title: target.title,
          status: target.status,
          progress: target.duration,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'No se pudieron cargar los cursos');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCourses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nextStep = getNextStep();
  const hasActiveCourse = !!currentCourseId;

  const quickLinks = [
    {
      title: 'Subir PDF',
      desc: 'Arrastra o selecciona tu documento',
      icon: CloudArrowUpIcon,
      to: '/upload',
      color: 'text-brand-600 bg-brand-50',
    },
    {
      title: 'Análisis IA',
      desc: 'Identifica temas, conceptos y objetivos',
      icon: BeakerIcon,
      to: hasActiveCourse ? `/analysis/${currentCourseId}` : '/analysis',
      color: 'text-violet-600 bg-violet-50',
    },
    {
      title: 'Diseño pedagógico',
      desc: 'Estructura educativa del curso',
      icon: AcademicCapIcon,
      to: hasActiveCourse ? `/pedagogical/${currentCourseId}` : '/pedagogical',
      color: 'text-sky-600 bg-sky-50',
    },
    {
      title: 'Revisar Guion',
      desc: 'Aprueba o regenera antes de generar',
      icon: DocumentTextIcon,
      to: hasActiveCourse ? `/script/${currentCourseId}` : '/script',
      color: 'text-emerald-600 bg-emerald-50',
    },
    {
      title: 'Ver Video',
      desc: 'Reproduce el curso generado',
      icon: VideoCameraIcon,
      to: hasActiveCourse ? `/video/${currentCourseId}` : '/video',
      color: 'text-rose-600 bg-rose-50',
    },
    {
      title: 'Calidad QA',
      desc: 'Puntuación y revisión automática',
      icon: ShieldCheckIcon,
      to: hasActiveCourse ? `/qa/${currentCourseId}` : '/qa',
      color: 'text-amber-600 bg-amber-50',
    },
  ];

  return (
    <div className="space-y-8">
      <section>
        {hasActiveCourse && nextStep ? (
          <div className="card bg-gradient-to-br from-brand-50 via-white to-violet-50 border-brand-200">
            <div className="flex flex-col md:flex-row md:items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="badge bg-brand-100 text-brand-700 font-semibold">
                    <SparklesIcon className="w-3.5 h-3.5" />
                    Curso activo
                  </span>
                  {currentCourseMeta?.status && (
                    <span className="badge bg-slate-100 text-slate-600">
                      Progreso: {currentCourseMeta.progress ?? 0}%
                    </span>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-1">
                  {currentCourseMeta?.title ||
                    `Curso en curso (${currentCourseId.slice(0, 8)}...)`}
                </h2>
                <p className="text-slate-600 mb-3 max-w-2xl">
                  Continúa al siguiente paso recomendado del flujo para avanzar
                  con la generación del video educativo.
                </p>
                {currentCourseMeta?.title && (
                  <button
                    onClick={clearCurrentCourse}
                    className="text-xs text-slate-500 hover:text-slate-700 underline"
                  >
                    Limpiar curso activo
                  </button>
                )}
              </div>
              <div className="shrink-0 md:w-[520px] w-full">
                <NextStepButton size="xl" block highlight />
              </div>
            </div>
          </div>
        ) : (
          <div className="card bg-gradient-to-br from-brand-50 to-white">
            <div className="flex flex-col md:flex-row md:items-center gap-6">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">
                  Convierte tus PDFs en videos educativos
                </h2>
                <p className="text-slate-600 mb-4 max-w-2xl">
                  Sube un documento académico y nuestra IA generará
                  automáticamente un curso en video con guion, avatar y
                  narración profesional en 6 pasos sencillos.
                </p>
              </div>
              <div className="shrink-0 md:w-[520px] w-full">
                <NextStepButton
                  overrideLabel="🚀 Comenzar nuevo curso"
                  description="Crea un nuevo registro de curso para iniciar el flujo de análisis, diseño, guion, video y QA"
                  overrideRoute="/upload"
                  size="xl" block highlight
                />
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="grid md:grid-cols-2 gap-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {quickLinks.map(({ title, desc, icon: Icon, to, color }) => (
            <Link
              key={title}
              to={to}
              className="card hover:shadow-md transition-shadow group"
            >
              <div
                className={`w-10 h-10 rounded-lg mb-3 flex items-center justify-center ${color}`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-slate-900 group-hover:text-brand-700 transition-colors">
                {title}
              </h3>
              <p className="text-sm text-slate-500 mt-1">{desc}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900">Tus cursos</h2>
          <div className="flex items-center gap-2">
            {courses.length > 0 && (
              <button
                onClick={loadCourses}
                className="btn-secondary text-sm"
                disabled={loading}
              >
                <ArrowRightIcon className="w-3.5 h-3.5 rotate-[-90deg]" />
                Actualizar
              </button>
            )}
            <Link to="/upload" className="btn btn-upload text-sm">
              <CloudArrowUpIcon className="w-4 h-4" />
              Nuevo curso
            </Link>
          </div>
        </div>

        {error && (
          <div className="card bg-rose-50 border-rose-200 text-rose-800">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="card animate-pulse"
                style={{ animationDelay: `${i * 120}ms` }}
              >
                <div className="aspect-video rounded-lg bg-slate-200 mb-4" />
                <div className="h-5 rounded bg-slate-200 mb-2 w-3/4" />
                <div className="h-4 rounded bg-slate-100 w-1/2" />
              </div>
            ))}
          </div>
        ) : courses.length === 0 ? (
          <div className="card text-center py-16">
            <CloudArrowUpIcon className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-1">
              Aún no tienes cursos
            </h3>
            <p className="text-slate-500 mb-6">
              Sube tu primer PDF para comenzar a generar videos educativos.
            </p>
            <Link to="/upload" className="btn btn-upload btn-xl pulse-highlight">
              <CloudArrowUpIcon className="w-5 h-5" />
              Subir PDF y crear primer curso
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                isActive={course.id === currentCourseId}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
