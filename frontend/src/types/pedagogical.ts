export interface LessonStructureItem {
  module: string;
  topics: string[];
  order: number;
  purpose?: string;
  duration_minutes?: number;
}

export interface Example {
  title: string;
  description: string;
  explanation?: string;
}

export interface CommonMistake {
  mistake: string;
  correction: string;
  context?: string;
}

export interface PedagogicalDesign {
  general_objective: string;
  specific_objectives: string[];
  prerequisites: string[];
  lesson_structure: LessonStructureItem[];
  examples: Example[];
  common_mistakes: CommonMistake[];
  summary: string;
  estimated_duration_minutes: number;
  activity_suggested?: string;
  teaching_strategies: string[];
  assessment_methods: string[];
}

export type PedagogicalOutput = PedagogicalDesign;
