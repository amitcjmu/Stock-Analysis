export interface SixRParameters {
  [key: string]: any;
}

export interface SixRRecommendation {
  id: string;
  recommendation: string;
  confidence: number;
  parameters: Record<string, any>;
}

export interface QuestionResponse {
  questionId: string;
  response: any;
}

export interface AnalysisProgress {
  status: 'idle' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  message?: string;
}

export interface Analysis {
  id: string;
  applicationId: string;
  status: string;
  parameters: SixRParameters;
  recommendation?: SixRRecommendation;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisQueueItem {
  id: string;
  name: string;
  applicationIds: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  progress: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  currentApp?: string;
}

export interface Application {
  id: string;
  name: string;
  description?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
} 