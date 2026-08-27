export type QASeverity = 'low' | 'medium' | 'high';
export type QAStatus = 'approved' | 'rejected';

export interface QAIssue {
  category: string;
  severity: QASeverity;
  description: string;
  suggestion?: string;
  scene_id?: number;
}

export interface QAResult {
  score: number;
  status: QAStatus | string;
  issues: QAIssue[];
  recommendations: string[];
  summary?: string;
}

export type QAOutput = QAResult;
