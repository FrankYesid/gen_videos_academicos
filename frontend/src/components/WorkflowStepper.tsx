import { Link } from 'react-router-dom';
import {
  CheckIcon,
  ArrowUpTrayIcon,
  BeakerIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import {
  useCurrentCourse,
  WORKFLOW_STEPS,
  type WorkflowStepKey,
} from '../contexts/CurrentCourseContext';

const ICONS: Record<WorkflowStepKey, typeof BeakerIcon> = {
  upload: ArrowUpTrayIcon,
  analysis: BeakerIcon,
  pedagogical: AcademicCapIcon,
  script: DocumentTextIcon,
  video: VideoCameraIcon,
  qa: ShieldCheckIcon,
};

export default function WorkflowStepper({
  compact = false,
}: {
  compact?: boolean;
}) {
  const ctx = useCurrentCourse();
  const currentStepKey = ctx.getCurrentStep();
  const getStepStatus = ctx.getStepStatus;
  const getRouteForStep = ctx.getRouteForStep;
  const currentCourseId = ctx.currentCourseId;

  return (
    <div className={`card-step bg-gradient-to-br from-slate-50 to-white ${compact ? 'p-4' : 'p-5 sm:p-6'}`}>
      {!compact && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
            Flujo de trabajo
          </h3>
          <span className="badge bg-brand-100 text-brand-700">
            {currentCourseId ? `Paso actual: ${currentStepKey}` : 'Paso 1/6: Crear curso'}
          </span>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-center gap-x-0 gap-y-3">
        {WORKFLOW_STEPS.map((step, idx) => {
          const status = getStepStatus(step.key);
          const route = getRouteForStep(step.key);
          const Icon = ICONS[step.key];
          const clickable =
            currentCourseId || step.key === 'upload' || status === 'done';

          const circleClass =
            status === 'done'
              ? 'step-circle-done'
              : status === 'current'
                ? 'step-circle-current pulse-highlight'
                : 'step-circle-pending';

          const lineClass =
            status === 'done' && idx < WORKFLOW_STEPS.length - 1
              ? 'step-line-done'
              : 'step-line-pending';

          const content = (
            <div className="step-item">
              <div className={circleClass}>
                {status === 'done' ? (
                  <CheckIcon className="w-5 h-5" />
                ) : (
                  <span className="flex items-center gap-1">
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{step.index}</span>
                  </span>
                )}
              </div>
              <div className="hidden md:block">
                <p
                  className={`text-xs font-bold ${
                    status === 'pending'
                      ? 'text-slate-400'
                      : status === 'current'
                        ? 'text-brand-700'
                        : 'text-emerald-700'
                  }`}
                >
                  {step.shortLabel}
                </p>
              </div>
            </div>
          );

          return (
            <div key={step.key} className="flex items-center">
              {clickable ? (
                <Link
                  to={route}
                  className="hover:scale-105 transition-transform"
                  title={step.label + ' - ' + step.description}
                >
                  {content}
                </Link>
              ) : (
                <span
                  className="cursor-not-allowed"
                  title={'Completa el paso anterior primero: ' + step.description}
                >
                  {content}
                </span>
              )}
              {idx < WORKFLOW_STEPS.length - 1 && (
                <div className={`${lineClass} mx-1 sm:mx-2`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
