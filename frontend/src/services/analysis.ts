import { get } from './api';

export interface Concept {
  concept: string;
  description: string;
  source_pages?: number[];
}

export interface Analysis {
  title: string;
  subject: string;
  level: string;
  language: string;
  summary: string;
  main_topics: string[];
  prerequisites: string[];
  concepts: Concept[];
  keywords: string[];
}

export async function getCourseAnalysis(courseId: string) {
  return get<Analysis>(`/courses/${courseId}/analysis`);
}
