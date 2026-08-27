import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import type { CourseStatus } from '../types/course';

export type WorkflowStepKey =
  | 'upload'
  | 'analysis'
  | 'pedagogical'
  | 'script'
  | 'video'
  | 'qa';

export interface WorkflowStepInfo {
  key: WorkflowStepKey;
  index: number;
  label: string;
  shortLabel: string;
  route: string;
  description: string;
  buttonLabel: string;
  color:
    | 'upload'
    | 'analysis'
    | 'pedagogical'
    | 'script'
    | 'video'
    | 'qa'
    | 'continue';
  requiresCourse: boolean;
}

export const WORKFLOW_STEPS: WorkflowStepInfo[] = [
  {
    key: 'upload',
    index: 1,
    label: 'Subir PDF / Crear curso',
    shortLabel: 'Subir',
    route: '/upload',
    description: 'Carga tu documento PDF o define un curso manualmente',
    buttonLabel: 'Subir PDF o crear curso',
    color: 'upload',
    requiresCourse: false,
  },
  {
    key: 'analysis',
    index: 2,
    label: 'Análisis de contenido IA',
    shortLabel: 'Análisis',
    route: '/analysis',
    description: 'Extrae temas clave, conceptos y objetivos educativos',
    buttonLabel: 'Realizar análisis →',
    color: 'analysis',
    requiresCourse: true,
  },
  {
    key: 'pedagogical',
    index: 3,
    label: 'Diseño pedagógico',
    shortLabel: 'Pedagógico',
    route: '/pedagogical',
    description: 'Estructura lecciones, ejemplos y estrategias didácticas',
    buttonLabel: 'Generar diseño pedagógico →',
    color: 'pedagogical',
    requiresCourse: true,
  },
  {
    key: 'script',
    index: 4,
    label: 'Guion con escenas',
    shortLabel: 'Guion',
    route: '/script',
    description: 'Crea escenas narrativas y visuales para cada lección',
    buttonLabel: 'Generar guion y escenas →',
    color: 'script',
    requiresCourse: true,
  },
  {
    key: 'video',
    index: 5,
    label: 'Generación de video',
    shortLabel: 'Video',
    route: '/video',
    description: 'Renderiza el video con avatar y narración profesional',
    buttonLabel: 'Generar video final →',
    color: 'video',
    requiresCourse: true,
  },
  {
    key: 'qa',
    index: 6,
    label: 'Revisión calidad QA',
    shortLabel: 'QA',
    route: '/qa',
    description: 'Puntuación automática y aprobación del curso',
    buttonLabel: 'Ver QA y resultados →',
    color: 'qa',
    requiresCourse: true,
  },
];

const STATUS_ORDER: Partial<Record<CourseStatus | string, number>> = {
  CREATED: 0,
  UPLOADED: 0,
  EXTRACTING: 1,
  ANALYZING: 1,
  PEDAGOGICAL_DESIGN: 2,
  SCRIPT_GENERATED: 3,
  SCRIPT_VALIDATED: 3.5,
  VIDEO_GENERATING: 4,
  VIDEO_PROCESSING: 4,
  VIDEO_READY: 4.5,
  QA: 5,
  COMPLETED: 6,
  FAILED: 0,
};

export interface NextStepInfo {
  key: WorkflowStepKey;
  step: WorkflowStepInfo;
  route: string;
  label: string;
  description: string;
}

interface CurrentCourseContextValue {
  currentCourseId: string | null;
  currentCourseTitle: string | null;
  currentCourseStatus: CourseStatus | string | null;
  progress: number | null;
  currentCourseMeta: {
    title?: string;
    status?: CourseStatus | string;
    progress?: number;
  };
  setCurrentCourse: (
    id: string,
    opts?: { title?: string; status?: CourseStatus | string; progress?: number },
  ) => void;
  updateCourseMeta: (opts: {
    title?: string | null;
    status?: CourseStatus | string | null;
    progress?: number | null;
  }) => void;
  clearCurrentCourse: () => void;
  getStepStatus: (
    step: WorkflowStepKey,
  ) => 'pending' | 'current' | 'done';
  getCurrentStep: () => WorkflowStepKey;
  getNextStep: () => NextStepInfo | null;
  getRouteForStep: (key: WorkflowStepKey) => string;
  steps: WorkflowStepInfo[];
  courseReady: boolean;
}

const STORAGE_KEY = 'acvg_current_course_v1';
const STORAGE_META_KEY = 'acvg_current_course_meta_v1';

interface CourseMeta {
  title?: string;
  status?: CourseStatus | string;
  progress?: number;
}

const CurrentCourseContext = createContext<CurrentCourseContextValue | null>(
  null,
);

export function CurrentCourseProvider({ children }: { children: ReactNode }) {
  const [currentCourseId, setIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });
  const [meta, setMeta] = useState<CourseMeta>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_META_KEY);
      return raw ? (JSON.parse(raw) as CourseMeta) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    try {
      if (currentCourseId) {
        localStorage.setItem(STORAGE_KEY, currentCourseId);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      /* ignore */
    }
  }, [currentCourseId]);

  useEffect(() => {
    try {
      if (Object.keys(meta).length > 0) {
        localStorage.setItem(STORAGE_META_KEY, JSON.stringify(meta));
      } else {
        localStorage.removeItem(STORAGE_META_KEY);
      }
    } catch {
      /* ignore */
    }
  }, [meta]);

  const setCurrentCourse = useCallback<
    CurrentCourseContextValue['setCurrentCourse']
  >((id, opts = {}) => {
    setIdState(id);
    setMeta({
      title: opts.title,
      status: opts.status,
      progress: opts.progress,
    });
  }, []);

  const updateCourseMeta = useCallback<
    CurrentCourseContextValue['updateCourseMeta']
  >((opts) => {
    setMeta((prev) => ({
      title: opts.title !== undefined ? (opts.title ?? undefined) : prev.title,
      status:
        opts.status !== undefined ? (opts.status ?? undefined) : prev.status,
      progress:
        opts.progress !== undefined
          ? (opts.progress ?? undefined)
          : prev.progress,
    }));
  }, []);

  const clearCurrentCourse = useCallback(() => {
    setIdState(null);
    setMeta({});
  }, []);

  const getStepStatus = useCallback<
    CurrentCourseContextValue['getStepStatus']
  >((step) => {
    const status = meta.status;
    const progress = meta.progress ?? 0;
    const statusIdx = status ? STATUS_ORDER[status] ?? -1 : -1;

    const stepStart = {
      upload: -1,
      analysis: 0,
      pedagogical: 1,
      script: 2,
      video: 3.5,
      qa: 4.5,
    }[step];

    const stepDoneAfter = {
      upload: 0,
      analysis: 1,
      pedagogical: 2,
      script: 3,
      video: 4.5,
      qa: 6,
    }[step];

    if (step === 'upload') {
      return currentCourseId ? 'done' : 'current';
    }

    if (statusIdx >= stepDoneAfter) {
      return 'done';
    }
    if (statusIdx >= stepStart) {
      return 'current';
    }
    const stepIdx = WORKFLOW_STEPS.findIndex((s) => s.key === step);
    if (stepIdx >= 0 && progress >= (stepIdx + 1) * 15) {
      return 'done';
    }
    return 'pending';
  }, [currentCourseId, meta.status, meta.progress]);

  const getCurrentStep = useCallback<
    CurrentCourseContextValue['getCurrentStep']
  >(() => {
    if (!currentCourseId) return 'upload';
    const candidates: WorkflowStepKey[] = [
      'qa',
      'video',
      'script',
      'pedagogical',
      'analysis',
    ];
    for (const c of candidates) {
      if (getStepStatus(c) === 'current') return c;
      if (getStepStatus(c) === 'pending') continue;
    }
    if (getStepStatus('qa') === 'done') return 'qa';
    return 'analysis';
  }, [currentCourseId, getStepStatus]);

  const getNextStep = useCallback<
    CurrentCourseContextValue['getNextStep']
  >(() => {
    if (!currentCourseId) {
      const step = WORKFLOW_STEPS[0];
      return {
        key: 'upload',
        step,
        route: step.route,
        label: 'Comenzar subiendo PDF',
        description: step.description,
      };
    }
    for (const step of WORKFLOW_STEPS) {
      const status = getStepStatus(step.key);
      if (status !== 'done') {
        return {
          key: step.key,
          step,
          route: currentCourseId ? `${step.route}/${currentCourseId}` : step.route,
          label: step.buttonLabel,
          description: step.description,
        };
      }
    }
    const step = WORKFLOW_STEPS[WORKFLOW_STEPS.length - 1];
    return {
      key: step.key,
      step,
      route: `${step.route}/${currentCourseId}`,
      label: 'Ver resultado final',
      description: step.description,
    };
  }, [currentCourseId, getStepStatus]);

  const getRouteForStep = useCallback<
    CurrentCourseContextValue['getRouteForStep']
  >(
    (key) => {
      const step = WORKFLOW_STEPS.find((s) => s.key === key)!;
      return currentCourseId ? `${step.route}/${currentCourseId}` : step.route;
    },
    [currentCourseId],
  );

  const value = useMemo<CurrentCourseContextValue>(
    () => ({
      currentCourseId,
      currentCourseTitle: meta.title ?? null,
      currentCourseStatus: meta.status ?? null,
      progress: meta.progress ?? null,
      currentCourseMeta: {
        title: meta.title,
        status: meta.status,
        progress: meta.progress,
      },
      setCurrentCourse,
      updateCourseMeta,
      clearCurrentCourse,
      getStepStatus,
      getCurrentStep,
      getNextStep,
      getRouteForStep,
      steps: WORKFLOW_STEPS,
      courseReady: Boolean(currentCourseId),
    }),
    [
      currentCourseId,
      meta.title,
      meta.status,
      meta.progress,
      setCurrentCourse,
      updateCourseMeta,
      clearCurrentCourse,
      getStepStatus,
      getCurrentStep,
      getNextStep,
      getRouteForStep,
    ],
  );

  return (
    <CurrentCourseContext.Provider value={value}>
      {children}
    </CurrentCourseContext.Provider>
  );
}

export function useCurrentCourse(): CurrentCourseContextValue {
  const ctx = useContext(CurrentCourseContext);
  if (!ctx) {
    throw new Error(
      'useCurrentCourse must be used within CurrentCourseProvider',
    );
  }
  return ctx;
}
