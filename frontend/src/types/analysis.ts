export interface Concept {
  concept: string;
  description: string;
  source_pages?: number[];
}

export interface Analysis {
  title: string;
  subject: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  language: string;
  summary: string;
  main_topics: string[];
  prerequisites: string[];
  concepts: Concept[];
  keywords: string[];
}
