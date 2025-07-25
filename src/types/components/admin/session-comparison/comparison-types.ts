/**
 * Session Comparison Types
 *
 * Session comparison and analysis types for comparison functionality.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../../shared';
import type { UserSession } from './session-types';
import type {
  SignificanceLevel,
  DifferenceCategory,
  SimilarityCategory,
  ImpactLevel,
  AssessmentLevel,
  RiskLevel,
  RecommendationType,
  PriorityLevel,
  EffortLevel
} from './enum-types';
import type { SessionFilter } from './filter-types'
import type { SessionComparisonColumn, ExportFormat } from './filter-types'

export interface SessionComparisonProps extends BaseComponentProps {
  sessions: UserSession[];
  onCompare: (sessionIds: string[]) => void;
  onRefresh?: () => void;
  loading?: boolean;
  error?: string | null;
  maxComparisons?: number;
  columns?: SessionComparisonColumn[];
  filters?: SessionFilter[];
  onFiltersChange?: (filters: Record<string, string | number | boolean | null>) => void;
  showDifferences?: boolean;
  showSimilarities?: boolean;
  showMetrics?: boolean;
  showTimeline?: boolean;
  showActivities?: boolean;
  showDeviceInfo?: boolean;
  showLocationInfo?: boolean;
  exportEnabled?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, sessions: UserSession[]) => void;
  renderSession?: (session: UserSession) => ReactNode;
  renderComparison?: (sessions: UserSession[]) => ReactNode;
  renderDifference?: (sessions: UserSession[], field: string) => ReactNode;
  renderMetric?: (sessions: UserSession[], metric: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'table' | 'side-by-side' | 'overlay' | 'detailed';
  layout?: 'horizontal' | 'vertical' | 'grid';
}

export interface SessionComparison {
  sessions: UserSession[];
  differences: ComparisonDifference[];
  similarities: ComparisonSimilarity[];
  metrics: ComparisonMetrics;
  summary: ComparisonSummary;
  recommendations: ComparisonRecommendation[];
}

export interface ComparisonDifference {
  field: string;
  label: string;
  values: ComparisonValue[];
  significance: SignificanceLevel;
  category: DifferenceCategory;
  impact: ImpactLevel;
}

export interface ComparisonSimilarity {
  field: string;
  label: string;
  value: unknown;
  confidence: number;
  category: SimilarityCategory;
}

export interface ComparisonValue {
  sessionId: string;
  value: unknown;
  normalized?: unknown;
  deviation?: number;
}

export interface ComparisonMetrics {
  overallSimilarity: number;
  behavioralSimilarity: number;
  temporalSimilarity: number;
  technicalSimilarity: number;
  securitySimilarity: number;
  riskDifferential: number;
  anomalyScore: number;
}

export interface ComparisonSummary {
  totalDifferences: number;
  significantDifferences: number;
  majorDifferences: number;
  minorDifferences: number;
  totalSimilarities: number;
  strongSimilarities: number;
  weakSimilarities: number;
  overallAssessment: AssessmentLevel;
  riskAssessment: RiskLevel;
}

export interface ComparisonRecommendation {
  id: string;
  type: RecommendationType;
  priority: PriorityLevel;
  title: string;
  description: string;
  rationale: string;
  actions: RecommendedAction[];
  impact: ImpactLevel;
  effort: EffortLevel;
}

export interface RecommendedAction {
  action: string;
  description: string;
  automated: boolean;
  parameters?: Record<string, string | number | boolean | null>;
}
