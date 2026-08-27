import { useNavigate } from 'react-router-dom';
import { SparklesIcon } from '@heroicons/react/24/outline';
import StatusBadge from './StatusBadge';

export interface CourseCardData {
  id: string;
  title: string;
  subject: string;
  status: string;
  duration: number;
  createdAt: string;
}

export default function CourseCard({
  course,
  isActive = false,
}: {
  course: CourseCardData;
  isActive?: boolean;
}) {
  const navigate = useNavigate();
  const date = new Date(course.createdAt).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
  const durationStr = course.duration
    ? `${Math.floor(course.duration / 60)} min ${course.duration % 60} s`
    : '—';

  function handleClick(e: React.MouseEvent) {
    e.preventDefault();
    if (course.status === 'COMPLETED') {
      navigate(`/video/${course.id}`);
    } else if (
      course.status === 'SCRIPT_VALIDATED' ||
      course.status === 'VIDEO_GENERATING' ||
      course.status === 'VIDEO_PROCESSING' ||
      course.status === 'VIDEO_READY'
    ) {
      navigate(`/video/${course.id}`);
    } else if (
      course.status === 'SCRIPT_GENERATED' ||
      course.status === 'PEDAGOGICAL_DESIGN'
    ) {
      navigate(`/script/${course.id}`);
    } else if (
      course.status === 'ANALYZING' ||
      course.status === 'EXTRACTING' ||
      course.status === 'UPLOADED' ||
      course.status === 'CREATED'
    ) {
      navigate(`/analysis/${course.id}`);
    } else {
      navigate(`/video/${course.id}`);
    }
  }

  return (
    <a
      href={`/video/${course.id}`}
      onClick={handleClick}
      className={`card group relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 ${
        isActive
          ? 'ring-2 ring-brand-500 border-brand-300 shadow-lg shadow-brand-500/10'
          : ''
      }`}
    >
      {isActive && (
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 rounded-full bg-gradient-to-r from-brand-500 to-brand-700 text-white px-3 py-1 text-[10px] font-bold uppercase tracking-wide shadow-md shadow-brand-500/30 pulse-highlight">
          <SparklesIcon className="w-3 h-3" />
          Curso activo
        </div>
      )}
      <div className="aspect-video rounded-lg bg-gradient-to-br from-slate-200 to-slate-100 mb-4 flex items-center justify-center overflow-hidden relative">
        <div className="text-xs text-slate-500 font-medium px-3 py-1 rounded-full bg-white/70 backdrop-blur-sm">
          {course.subject}
        </div>
      </div>
      <h3 className="font-semibold text-slate-900 group-hover:text-brand-700 transition-colors mb-2 line-clamp-2">
        {course.title}
      </h3>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{date}</span>
        <span>{durationStr}</span>
      </div>
      <div className="mt-3">
        <StatusBadge status={course.status} />
      </div>
    </a>
  );
}
