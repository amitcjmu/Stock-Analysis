/**
 * Analysis Component Types
 *
 * Types for crew analysis panels, training progress, and analysis-related functionality.
 */

import type { ReactNode } from 'react';
import type { BaseDiscoveryProps, LogLevel } from './base-types';
import type { ExportFormat } from './data-import-types';

// Analysis component types
export interface CrewAnalysisPanelProps extends BaseDiscoveryProps {
  analysis: CrewAnalysis[];
  onTriggerAnalysis: () => void;
  loading?: boolean;
  error?: string | null;
  analysisTypes?: AnalysisType[];
  selectedAnalysisType?: string;
  onAnalysisTypeChange?: (type: string) => void;
  parameters?: AnalysisParameters;
  onParametersChange?: (parameters: AnalysisParameters) => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  enableComparison?: boolean;
  comparisonBaseline?: string;
  onComparisonBaselineChange?: (baseline: string) => void;
  enableExport?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, data: CrewAnalysis[]) => void;
  enableSharing?: boolean;
  onShare?: (analysis: CrewAnalysis[]) => void;
  customActions?: AnalysisAction[];
  onCustomAction?: (action: AnalysisAction, analysis: CrewAnalysis[]) => void;
  layout?: 'list' | 'grid' | 'timeline' | 'chart';
  gridColumns?: number;
  chartType?: ChartType;
  onChartTypeChange?: (type: ChartType) => void;
  filters?: AnalysisFilter[];
  onFilterChange?: (filters: AnalysisFilter[]) => void;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  showDetails?: boolean;
  onToggleDetails?: () => void;
  expandedItems?: string[];
  onItemExpand?: (itemId: string) => void;
  renderAnalysisItem?: (analysis: CrewAnalysis) => ReactNode;
  renderAnalysisDetails?: (analysis: CrewAnalysis) => ReactNode;
}

export interface TrainingProgressTabProps extends BaseDiscoveryProps {
  progress: TrainingProgress;
  onProgressUpdate: (updates: Partial<TrainingProgress>) => void;
  flowId: string;
  enableTraining?: boolean;
  onStartTraining?: () => void;
  onStopTraining?: () => void;
  onPauseTraining?: () => void;
  onResumeTraining?: () => void;
  trainingStatus?: TrainingStatus;
  trainingMetrics?: TrainingMetrics;
  onMetricsRefresh?: () => void;
  enableModelComparison?: boolean;
  availableModels?: ModelInfo[];
  selectedModel?: string;
  onModelSelect?: (modelId: string) => void;
  enableHyperparameterTuning?: boolean;
  hyperparameters?: Hyperparameters;
  onHyperparameterChange?: (params: Hyperparameters) => void;
  enableDatasetManagement?: boolean;
  datasets?: Dataset[];
  selectedDataset?: string;
  onDatasetSelect?: (datasetId: string) => void;
  onDatasetUpload?: (files: File[]) => void;
  enableValidation?: boolean;
  validationConfig?: ValidationConfig;
  onValidationConfigChange?: (config: ValidationConfig) => void;
  enableExport?: boolean;
  onExportModel?: () => void;
  onExportMetrics?: () => void;
  customActions?: TrainingAction[];
  onCustomAction?: (action: TrainingAction) => void;
  chartConfig?: ChartConfig;
  onChartConfigChange?: (config: ChartConfig) => void;
  showLogs?: boolean;
  logs?: TrainingLog[];
  onLogsRefresh?: () => void;
  logLevel?: LogLevel;
  onLogLevelChange?: (level: LogLevel) => void;
}

// Supporting types
export interface CrewAnalysis {
  id: string;
  analysisType: string;
  findings: AnalysisFinding[];
  recommendations: string[];
  confidence: number;
  executedAt: string;
  executedBy: string;
  status: 'completed' | 'in_progress' | 'failed';
  metadata: Record<string, string | number | boolean | null>;
}

export interface TrainingProgress {
  totalSamples: number;
  processedSamples: number;
  accuracy: number;
  lastTrainingRun: string;
  modelVersion: string;
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  elapsedTime: number;
  estimatedTimeRemaining?: number;
  currentEpoch: number;
  totalEpochs: number;
  loss: number;
  validationLoss?: number;
  metrics: Record<string, number>;
}

export interface AnalysisType {
  id: string;
  name: string;
  description?: string;
  parameters?: AnalysisParameter[];
  icon?: string | ReactNode;
}

export interface AnalysisParameters {
  [key: string]: unknown;
}

export interface AnalysisParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect';
  label: string;
  description?: string;
  required?: boolean;
  defaultValue?: unknown;
  options?: Array<{ value: unknown; label: string }>;
  min?: number;
  max?: number;
  step?: number;
}

export interface AnalysisAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: (analysis: CrewAnalysis[]) => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface ChartType {
  id: string;
  name: string;
  icon?: string | ReactNode;
  config?: Record<string, string | number | boolean | null>;
}

export interface AnalysisFilter {
  field: string;
  operator: string;
  value: unknown;
  label?: string;
  enabled?: boolean;
}

export interface AnalysisFinding {
  type: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
  impact: string;
  confidence: number;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface TrainingStatus {
  status: 'idle' | 'training' | 'paused' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  progress: number;
  currentEpoch: number;
  totalEpochs: number;
  message?: string;
}

export interface TrainingMetrics {
  accuracy: number;
  loss: number;
  validationAccuracy?: number;
  validationLoss?: number;
  precision?: number;
  recall?: number;
  f1Score?: number;
  customMetrics?: Record<string, number>;
  history: MetricHistory[];
}

export interface MetricHistory {
  epoch: number;
  timestamp: string;
  metrics: Record<string, number>;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  description?: string;
  architecture: string;
  parameters: number;
  trainingData?: string;
  accuracy?: number;
  size: number;
  createdAt: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface Hyperparameters {
  learningRate: number;
  batchSize: number;
  epochs: number;
  optimizer: string;
  momentum?: number;
  weightDecay?: number;
  dropout?: number;
  hiddenLayers?: number;
  hiddenUnits?: number;
  activationFunction?: string;
  lossFunction?: string;
  customParameters?: Record<string, string | number | boolean | null>;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  size: number;
  recordCount: number;
  features: number;
  labels?: string[];
  splitRatio?: { train: number; validation: number; test: number };
  createdAt: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface ValidationConfig {
  enabled: boolean;
  splitRatio: number;
  stratified: boolean;
  crossValidation: boolean;
  folds?: number;
  metrics: string[];
  earlyStoppingEnabled: boolean;
  patience?: number;
  minDelta?: number;
}

export interface TrainingAction {
  id: string;
  label: string;
  icon?: string | ReactNode;
  handler: () => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface ChartConfig {
  chartType: string;
  metrics: string[];
  timeRange: string;
  aggregation: string;
  showLegend: boolean;
  showGrid: boolean;
  colors: string[];
  width?: number;
  height?: number;
}

export interface TrainingLog {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source?: string;
  metadata?: Record<string, string | number | boolean | null>;
}
