import { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRightIcon,
  BeakerIcon,
  AcademicCapIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  ShieldCheckIcon,
  ArrowUpTrayIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import {
  useCurrentCourse,
  type WorkflowStepKey,
} from '../contexts/CurrentCourseContext';

const ICONS: Record<WorkflowStepKey | 'continue', typeof ArrowRightIcon> = {
  upload: ArrowUpTrayIcon,
  analysis: BeakerIcon,
  pedagogical: AcademicCapIcon,
  script: DocumentTextIcon,
  video: VideoCameraIcon,
  qa: ShieldCheckIcon,
  continue: ArrowRightIcon,
};

const BTN_CLASS: Record<WorkflowStepKey | 'continue', string> = {
  upload: 'btn-upload',
  analysis: 'btn-analysis',
  pedagogical: 'btn-pedagogical',
  script: 'btn-script',
  video: 'btn-video',
  qa: 'btn-qa',
  continue: 'btn-continue',
};

export interface NextStepButtonProps {
  overrideLabel?: string;
  overrideRoute?: string;
  onClick?: () => Promise<void> | void;
  loading?: boolean;
  loadingText?: string;
  size?: 'lg' | 'xl';
  block?: boolean;
  highlight?: boolean;
  disabled?: boolean;
  description?: string;
  icon?: ReactNode;
}

export default function NextStepButton({
  overrideLabel,
  overrideRoute,
  onClick,
  loading = false,
  loadingText,
  size = 'xl',
  block = true,
  highlight = true,
  disabled = false,
  description,
  icon,
}: NextStepButtonProps) {
  const { getNextStep } = useCurrentCourse();
  const navigate = useNavigate();
  const next = getNextStep();
  const route = overrideRoute ?? next?.route ?? '/upload';
  const rawLabel = overrideLabel ?? next?.label ?? 'Continuar al siguiente paso';
  const kind = next?.step.color ?? 'continue';
  const desc = description ?? next?.description;

  const StepIcon = ICONS[kind];

  const sizeClass = size === 'xl' ? 'btn-xl' : 'btn-lg';
  const btnClass = `${BTN_CLASS[kind]} ${sizeClass} ${block ? 'btn-block' : ''} ${highlight && !disabled ? 'pulse-highlight' : ''}`;

  const finalLabel = loading && loadingText ? loadingText : rawLabel;
  const finalDisabled = disabled || loading;

  const content = (
    <div className="flex flex-col items-start gap-1 text-left w-full">
      <div className="flex items-center gap-2.5 w-full">
        {icon ?? <StepIcon className="w-5 h-5 shrink-0" />}
        <span className="flex-1">{finalLabel}</span>
        <ArrowRightIcon className="w-5 h-5 shrink-0 animate-pulse" />
      </div>
      {desc && (
        <p className={`text-xs font-normal w-full pl-8 ${
          kind === 'continue'
            ? 'text-slate-300/80'
            : 'text-white/85'
        }`}>
          {desc}
        </p>
      )}
    </div>
  );

  const handleClick = async (e: React.MouseEvent) => {
    if (finalDisabled) {
      e.preventDefault();
      return;
    }
    if (onClick) {
      e.preventDefault();
      try {
        await onClick();
      } catch {
        return;
      }
      navigate(route);
    }
  };

  if (onClick) {
    return (
      <button
        type="button"
        onClick={handleClick}
        disabled={finalDisabled}
        className={btnClass}
        title={desc ?? rawLabel}
      >
        {loading ? <SparklesIcon className="w-5 h-5 shrink-0 animate-spin" /> : null}
        <div className="flex flex-col items-start gap-1 text-left w-full">
          <div className="flex items-center gap-2.5 w-full">
            {!loading && (icon ?? <StepIcon className="w-5 h-5 shrink-0" />)}
            <span className="flex-1">{finalLabel}</span>
            {!loading && <ArrowRightIcon className="w-5 h-5 shrink-0 animate-pulse" />}
          </div>
          {desc && (
            <p className={`text-xs font-normal w-full pl-8 ${
              kind === 'continue'
                ? 'text-slate-300/80'
                : 'text-white/85'
            }`}>
              {desc}
            </p>
          )}
        </div>
      </button>
    );
  }

  return (
    <Link
      to={route}
      onClick={(e) => {
        if (finalDisabled) e.preventDefault();
      }}
      className={`${btnClass} no-underline ${finalDisabled ? 'pointer-events-none' : ''}`}
      aria-disabled={finalDisabled}
      title={desc ?? rawLabel}
    >
      {content}
    </Link>
  );
}
