import type { Script } from './script';
import type { PedagogicalDesign } from './pedagogical';
import type { QAResult } from './qa';

export type CourseStatus =
  | 'CREATED'
  | 'UPLOADED'
  | 'EXTRACTING'
  | 'ANALYZING'
  | 'PEDAGOGICAL_DESIGN'
  | 'SCRIPT_GENERATED'
  | 'SCRIPT_VALIDATED'
  | 'VIDEO_GENERATING'
  | 'VIDEO_PROCESSING'
  | 'VIDEO_READY'
  | 'QA'
  | 'COMPLETED'
  | 'FAILED';

export interface CourseListItem {
  id: string;
  title?: string;
  subject?: string;
  level?: string;
  language: string;
  status: CourseStatus | string;
  progress: number;
  script_approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface Course {
  id: string;
  document_id?: string;
  title?: string;
  description?: string;
  subject?: string;
  level?: string;
  language?: string;
  status: CourseStatus | string;
  progress?: number;
  current_step?: string;
  script_approved?: boolean;
  qa_score?: number;
  qa_status?: string;
  created_at: string;
  updated_at: string;
  pedagogical_data?: PedagogicalDesign | null;
  script_data?: Script | null;
  qa_data?: QAResult | null;
  error_message?: string;
  estimated_duration_minutes?: number;
  main_topics?: string[];
  prerequisites?: string[];
  concepts?: any[];
  keywords?: string[];
}

export type FullCourse = Course;
